# coding: spec

from photons_transport.fake import Attrs

from photons_app.test_helpers import TestCase

from noseOfYeti.tokeniser.support import noy_sup_setUp
from unittest import mock

describe TestCase, "Attrs":
    before_each:
        self.device = mock.Mock(name="device")
        self.attrs = Attrs(self.device)

    it "takes in a device":
        self.assertEqual(self.attrs._attrs, {})
        self.assertIs(self.attrs._device, self.device)

    it "can use dictionary syntax":
        val = mock.Mock(name="val")
        key = mock.Mock(name="key")
        self.attrs[key] = val
        self.device.validate_attr.assert_called_once_with(key, val)
        self.assertIs(self.attrs[key], val)

        self.device.validate_attr.reset_mock()
        val2 = mock.Mock(name="val")
        key2 = mock.Mock(name="key")
        self.attrs[key2] = val2
        self.device.validate_attr.assert_called_once_with(key2, val2)
        self.assertIs(self.attrs[key], val)
        self.assertIs(self.attrs[key2], val2)

    it "can use object syntax":
        val = mock.Mock(name="val")
        self.attrs.wat = val
        self.device.validate_attr.assert_called_once_with("wat", val)
        self.assertIs(self.attrs.wat, val)

        self.device.validate_attr.reset_mock()
        val2 = mock.Mock(name="val")
        self.attrs.wat2 = val2
        self.device.validate_attr.assert_called_once_with("wat2", val2)
        self.assertIs(self.attrs.wat, val)
        self.assertIs(self.attrs.wat2, val2)

    it "doesn't set key if validate_attr raises an error":
        self.assertEqual(self.attrs._attrs, {})

        self.attrs.wat = 2
        self.attrs["things"] = 3
        expected = {"wat": 2, "things": 3}
        self.assertEqual(self.attrs._attrs, expected)

        self.device.validate_attr.side_effect = ValueError("NOPE")

        with self.fuzzyAssertRaisesError(ValueError, "NOPE"):
            self.attrs.nope = 2

        with self.fuzzyAssertRaisesError(AttributeError):
            self.attrs.nope

        with self.fuzzyAssertRaisesError(ValueError, "NOPE"):
            self.attrs["hello"] = 3

        with self.fuzzyAssertRaisesError(KeyError):
            self.attrs["hello"]
