# coding: spec

from unittest import mock

import pytest
from interactor.commander.store import load_commands, store
from photons_app import helpers as hp
from photons_app.mimic.event import Events


@pytest.fixture()
def store_clone():
    load_commands()
    return store.clone()


@pytest.fixture()
def final_future():
    fut = hp.create_future()
    try:
        yield fut
    finally:
        fut.cancel()


@pytest.fixture()
async def sender(devices, final_future):
    async with devices.for_test(final_future) as sender:
        yield sender


@pytest.fixture()
async def server(
    store_clone, devices, server_wrapper, sender, final_future, FakeTime, MockedCallLater
):
    with FakeTime() as t:
        async with MockedCallLater(t):
            async with server_wrapper(store_clone, sender, final_future) as server:

                async with server.server.database.engine.begin() as conn:
                    await conn.run_sync(server.server.database.Base.metadata.create_all)

                yield server


describe "Scene Commands":

    # sqlite is very slow on github actions for some reason
    @pytest.mark.async_timeout(20)
    async it "has scene commands", devices, server, responses:
        await server.assertCommand("/v1/lifx/command", {"command": "scene_info"}, json_output={})

        scene_capture = {
            "meta": mock.ANY,
            "scene": [
                {
                    "color": mock.ANY,
                    "matcher": {"serial": devices["a19_1"].serial},
                    "power": False,
                },
                {
                    "color": mock.ANY,
                    "matcher": {"serial": devices["a19_2"].serial},
                    "power": True,
                },
                {
                    "color": mock.ANY,
                    "matcher": {"serial": devices["color1000"].serial},
                    "power": True,
                },
                {
                    "color": mock.ANY,
                    "matcher": {"serial": devices["white800"].serial},
                    "power": True,
                },
                {
                    "zones": mock.ANY,
                    "matcher": {"serial": devices["strip1"].serial},
                    "power": True,
                },
                {
                    "zones": mock.ANY,
                    "matcher": {"serial": devices["strip2"].serial},
                    "power": True,
                },
                {
                    "chain": mock.ANY,
                    "matcher": {"serial": devices["candle"].serial},
                    "power": True,
                },
                {
                    "chain": mock.ANY,
                    "matcher": {"serial": devices["tile"].serial},
                    "power": True,
                },
                {
                    "color": mock.ANY,
                    "matcher": {"serial": devices["clean"].serial},
                    "power": True,
                },
            ],
        }

        got = await server.assertCommand(
            "/v1/lifx/command", {"command": "scene_capture"}, json_output=scene_capture
        )

        got2 = await server.assertCommand(
            "/v1/lifx/command", {"command": "scene_capture"}, json_output=scene_capture
        )

        assert got["meta"]["uuid"] != got2["meta"]["uuid"]
        await server.assertCommand(
            "/v1/lifx/command",
            {"command": "scene_info"},
            json_output={
                got["meta"]["uuid"]: got,
                got2["meta"]["uuid"]: got2,
            },
        )

        assert not got["scene"][0]["power"]
        await devices["a19_1"].change_one("power", 65535, event=None)
        server.server.sender.gatherer.clear_cache()

        got["scene"][0]["power"] = True
        got3 = await server.assertCommand(
            "/v1/lifx/command",
            {"command": "scene_capture", "args": {"uuid": got["meta"]["uuid"]}},
            json_output=got,
        )
        assert got == got3

        await server.assertCommand(
            "/v1/lifx/command",
            {"command": "scene_info"},
            json_output={
                got["meta"]["uuid"]: got3,
                got2["meta"]["uuid"]: got2,
            },
        )

        got["scene"][1]["color"] = "green"
        await server.assertCommand(
            "/v1/lifx/command",
            {
                "command": "scene_change",
                "args": {"uuid": got["meta"]["uuid"], "scene": got["scene"]},
            },
            text_output=got["meta"]["uuid"].encode(),
        )
        await server.assertCommand(
            "/v1/lifx/command",
            {"command": "scene_info"},
            json_output={
                got["meta"]["uuid"]: got,
                got2["meta"]["uuid"]: got2,
            },
        )

        await server.assertCommand(
            "/v1/lifx/command",
            {"command": "scene_delete", "args": {"uuid": got["meta"]["uuid"]}},
            json_output={"deleted": True, "uuid": [got["meta"]["uuid"]]},
        )

        await server.assertCommand(
            "/v1/lifx/command",
            {"command": "scene_info"},
            json_output={got2["meta"]["uuid"]: got2},
        )

        # Very naive test
        for d in devices:
            devices.store(d).clear()

        await server.assertCommand(
            "/v1/lifx/command",
            {"command": "scene_apply", "args": {"uuid": got2["meta"]["uuid"]}},
            json_output={"results": {d.serial: "ok" for d in devices if d.cap.is_light}},
        )

        for d in devices:
            if not d.cap.is_light:
                continue

            assert any(
                event | Events.ATTRIBUTE_CHANGE for event in devices.store(d)
            ), devices.store(d)

        # Very naive test with an override that is None
        for d in devices:
            devices.store(d).clear()

        await server.assertCommand(
            "/v1/lifx/command",
            {
                "command": "scene_apply",
                "args": {"uuid": got2["meta"]["uuid"], "overrides": {"kelvin": None}},
            },
            json_output={"results": {d.serial: "ok" for d in devices if d.cap.is_light}},
        )

        for d in devices:
            if not d.cap.is_light:
                continue

            assert any(
                event | Events.ATTRIBUTE_CHANGE for event in devices.store(d)
            ), devices.store(d)
