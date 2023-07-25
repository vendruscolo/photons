# coding: spec

import os
from unittest import mock

from delfick_project.errors_pytest import assertRaises
from photons_app import helpers as hp
from photons_messages import fields

describe "future to string":
    it "just repr's a not future":

        class Thing:
            def __repr__(s):
                return "<REPR THING>"

        assert hp.fut_to_string(Thing()) == "<REPR THING>"

    it "says if the future is pending":
        fut = hp.create_future(name="one")
        assert hp.fut_to_string(fut) == "<Future#one(pending)>"

        fut = hp.create_future()
        assert hp.fut_to_string(fut) == "<Future#None(pending)>"

    it "says if the future is cancelled":
        fut = hp.create_future(name="one")
        fut.cancel()
        assert hp.fut_to_string(fut) == "<Future#one(cancelled)>"

        fut = hp.create_future()
        fut.cancel()
        assert hp.fut_to_string(fut) == "<Future#None(cancelled)>"

    it "says if the future has an exception":
        fut = hp.create_future(name="one")
        fut.set_exception(ValueError("HI"))
        assert hp.fut_to_string(fut) == "<Future#one(exception:ValueError:HI)>"

        fut = hp.create_future()
        fut.set_exception(TypeError("NOPE"))
        assert hp.fut_to_string(fut) == "<Future#None(exception:TypeError:NOPE)>"

    it "says if the future has a result":
        fut = hp.create_future(name="one")
        fut.set_result(True)
        assert hp.fut_to_string(fut) == "<Future#one(result)>"

        fut = hp.create_future()
        fut.set_result(False)
        assert hp.fut_to_string(fut) == "<Future#None(result)>"

describe "add_error":
    it "calls the error_catcher with the error if it's a callable":
        error = mock.Mock(name="error")
        catcher = mock.Mock(name="catcher")
        hp.add_error(catcher, error)
        catcher.assert_called_once_with(error)

    it "appends to the error catcher if it's a list":
        error = mock.Mock(name="error")
        catcher = []
        hp.add_error(catcher, error)
        assert catcher == [error]

    it "adds to the error catcher if it's a set":
        error = mock.Mock(name="error")
        catcher = set()
        hp.add_error(catcher, error)
        assert catcher == set([error])

describe "a_temp_file":
    it "gives us the tmpfile":
        with hp.a_temp_file() as fle:
            fle.write(b"wassup")
            fle.seek(0)
            assert os.path.exists(fle.name)
            assert fle.read() == b"wassup"
        assert not os.path.exists(fle.name)

    it "doesn't fail if we delete the file early":
        with hp.a_temp_file() as fle:
            fle.close()
            os.remove(fle.name)
        assert not os.path.exists(fle.name)

describe "just_log_exceptions":
    it "logs exceptions":
        log = mock.Mock(name="log")

        error = ValueError("NOPE")
        with hp.just_log_exceptions(log):
            raise error

        log.error.assert_called_once_with(
            "Unexpected error", exc_info=(ValueError, error, mock.ANY)
        )

    it "can be given a different message":
        log = mock.Mock(name="log")

        error = ValueError("NOPE")
        with hp.just_log_exceptions(log, message="a different message"):
            raise error

        log.error.assert_called_once_with(
            "a different message", exc_info=(ValueError, error, mock.ANY)
        )

    it "can reraise particular errors":
        log = mock.Mock(name="log")

        error = ValueError("NOPE")
        with hp.just_log_exceptions(log, message="a different message", reraise=[TypeError]):
            raise error

        log.error.assert_called_once_with(
            "a different message", exc_info=(ValueError, error, mock.ANY)
        )
        log.error.reset_mock()

        with assertRaises(TypeError, "wat"):
            with hp.just_log_exceptions(log, message="a different message", reraise=[TypeError]):
                raise TypeError("wat")

        log.assert_not_called()

describe "nested_dict_retrieve":
    it "returns us the dflt if we can't find the key":
        data = {"one": {"two": {"three": 3}}}
        dflt = mock.Mock(name="dflt")
        for keys in (
            ["one", "four"],
            ["four", "five"],
            ["one", "two", "five"],
            ["one", "two", "three", "four"],
        ):
            assert hp.nested_dict_retrieve(data, keys, dflt) is dflt

    it "returns us what it finds":
        data = {"one": {"two": {"three": 3}}}
        dflt = mock.Mock(name="dflt")

        assert hp.nested_dict_retrieve(data, [], dflt) == data
        assert hp.nested_dict_retrieve(data, ["one"], dflt) == {"two": {"three": 3}}
        assert hp.nested_dict_retrieve(data, ["one", "two"], dflt) == {"three": 3}
        assert hp.nested_dict_retrieve(data, ["one", "two", "three"], dflt) == 3

describe "memoized_property":
    it "caches on the instance":
        called = []
        blah = mock.Mock(name="blah")

        class Thing:
            @hp.memoized_property
            def blah(s):
                called.append(1)
                return blah

        thing = Thing()
        assert called == []
        assert thing.blah is blah
        assert called == [1]

        assert thing._blah == blah
        assert thing.blah is blah
        assert called == [1]

    it "caches on the instance if the return is None":
        called = []

        class Thing:
            @hp.memoized_property
            def blah(s):
                called.append(1)
                return None

        thing = Thing()
        assert called == []
        assert thing.blah is None
        assert called == [1]

        assert thing._blah is None
        assert thing.blah is None
        assert called == [1]

    it "caches on the instance if the return is False":
        called = []

        class Thing:
            @hp.memoized_property
            def blah(s):
                called.append(1)
                return False

        thing = Thing()
        assert called == []
        assert thing.blah is False
        assert called == [1]

        assert thing._blah is False
        assert thing.blah is False
        assert called == [1]

    it "can set the value":
        called = []
        blah = mock.Mock(name="blah")
        meh = mock.Mock(name="meh")

        class Thing:
            @hp.memoized_property
            def blah(s):
                called.append(1)
                return blah

        thing = Thing()
        assert called == []
        assert thing.blah is blah
        assert called == [1]

        assert thing._blah == blah
        thing.blah = meh
        assert thing._blah == meh

        assert thing.blah is meh
        assert called == [1]

    it "can delete the cache":
        called = []
        blah = mock.Mock(name="blah")

        class Thing:
            @hp.memoized_property
            def blah(s):
                called.append(1)
                return blah

        thing = Thing()
        assert called == []
        assert thing.blah is blah
        assert called == [1]

        assert thing._blah == blah
        assert thing.blah is blah
        assert called == [1]

        del thing.blah
        assert not hasattr(thing, "_blah")

        assert thing.blah is blah
        assert called == [1, 1]

describe "Color":
    it "can be made and cloned":
        c1 = hp.Color(2, 0, 0.3, 3500)
        c2 = c1.clone()

        assert c1 is not c2

        for c in (c1, c2):
            assert c.hue == 2
            assert c["hue"] == 2

            assert c.saturation == 0
            assert c["saturation"] == 0

            assert c.brightness == 0.3
            assert c["brightness"] == 0.3

            assert c.kelvin == 3500
            assert c["kelvin"] == 3500

        c2.hue = 45
        c2.brightness = 1
        assert c2 == hp.Color(45, 0, 1, 3500)
        assert c1 == hp.Color(2, 0, 0.3, 3500)
        assert c1.as_dict() == {"hue": 2, "saturation": 0, "brightness": 0.3, "kelvin": 3500}

    it "can be compared with a tuple":
        assert hp.Color(2, 0, 0, 3500) != (2,)
        assert hp.Color(2, 0, 0, 3500) != (2, 0)
        assert hp.Color(2, 0, 0, 3500) != (2, 0, 0)
        assert hp.Color(2, 0, 0, 3500) == (2, 0, 0, 3500)

        assert hp.Color(2, 0, 0, 3500) != (20, 0, 0, 3500)
        assert hp.Color(2, 0, 0, 3500) != (2, 1, 0, 3500)
        assert hp.Color(2, 0, 0, 3500) != (2, 0, 1, 3500)
        assert hp.Color(2, 0, 0, 3500) != (2, 0, 0, 3700)

    it "can be compared with a dictionary":
        assert hp.Color(2, 0, 0, 3500) != {"hue": 2}
        assert hp.Color(2, 0, 0, 3500) != {"hue": 2, "saturation": 0}
        assert hp.Color(2, 0, 0, 3500) != {"hue": 2, "saturation": 0, "brightness": 0}
        assert hp.Color(2, 0, 0, 3500) == {
            "hue": 2,
            "saturation": 0,
            "brightness": 0,
            "kelvin": 3500,
        }

        assert hp.Color(2, 0, 0, 3500) != {
            "hue": 20,
            "saturation": 0,
            "brightness": 0,
            "kelvin": 3500,
        }
        assert hp.Color(2, 0, 0, 3500) != {
            "hue": 2,
            "saturation": 1,
            "brightness": 0,
            "kelvin": 3500,
        }
        assert hp.Color(2, 0, 0, 3500) != {
            "hue": 2,
            "saturation": 0,
            "brightness": 1,
            "kelvin": 3500,
        }
        assert hp.Color(2, 0, 0, 3500) != {
            "hue": 2,
            "saturation": 0,
            "brightness": 0,
            "kelvin": 3700,
        }

    it "can be compared with another hp.Color":
        assert hp.Color(2, 0, 0, 3500) == hp.Color(2, 0, 0, 3500)

        assert hp.Color(2, 0, 0, 3500) != hp.Color(20, 0, 0, 3500)
        assert hp.Color(2, 0, 0, 3500) != hp.Color(2, 1, 0, 3500)
        assert hp.Color(2, 0, 0, 3500) != hp.Color(2, 0, 1, 3500)
        assert hp.Color(2, 0, 0, 3500) != hp.Color(2, 0, 0, 3700)

    it "can be compared with a real fields.Color":
        assert hp.Color(2, 0, 0, 3500) == fields.Color(
            hue=2, saturation=0, brightness=0, kelvin=3500
        )

        assert hp.Color(2, 0, 0, 3500) != fields.Color(
            hue=20, saturation=0, brightness=0, kelvin=3500
        )
        assert hp.Color(2, 0, 0, 3500) != fields.Color(
            hue=2, saturation=1, brightness=0, kelvin=3500
        )
        assert hp.Color(2, 0, 0, 3500) != fields.Color(
            hue=2, saturation=0, brightness=1, kelvin=3500
        )
        assert hp.Color(2, 0, 0, 3500) != fields.Color(
            hue=2, saturation=0, brightness=0, kelvin=3700
        )

    it "compares to 4 decimal places":
        assert hp.Color(250.245677, 0.134577, 0.765477, 4568) == (
            250.245699,
            0.134599,
            0.765499,
            4568,
        )
        assert hp.Color(250.245677, 0.134577, 0.765477, 4568) != (
            250.245799,
            0.134699,
            0.765599,
            4568,
        )

    it "compares hue 359.99 to hue 0.0":
        assert hp.Color(359.99, 1.0, 1.0, 3500) == (
            0.0,
            1.0,
            1.0,
            3500,
        )
