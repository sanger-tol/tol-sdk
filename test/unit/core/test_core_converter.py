# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import IsolatedAsyncioTestCase
from unittest.mock import Mock, call, create_autospec

from tol.core.core_converter import AsyncConverter


class TestAsyncConverter(IsolatedAsyncioTestCase):
    """
    `AsyncConverter` behaves as expected, given a suitable
    mock for `AsyncConverter().async_convert()`
    """

    async def test_async_convert_optional_none(self):
        """
        `AsyncConverter().async_convert_optional()` with
        both None input
        """

        expected = Mock()

        mock_converter = create_autospec(AsyncConverter, spec_set=True)
        mock_converter.async_convert.side_effect = lambda _: expected

        observed = await AsyncConverter.async_convert_optional(
            mock_converter,
            None
        )

        mock_converter.async_convert.assert_not_called()
        assert observed is None

    async def test_async_convert_optional_populated(self):
        """
        `AsyncConverter().async_convert_optional()` with
        a populated input
        """

        expected = Mock()

        input_ = Mock()

        mock_converter = create_autospec(AsyncConverter, spec_set=True)
        mock_converter.async_convert.side_effect = lambda _: expected

        observed = await AsyncConverter.async_convert_optional(
            mock_converter,
            input_
        )

        mock_converter.async_convert.assert_called_once_with(input_)
        assert observed == expected

    async def test_async_convert_iterable_empty(self):
        """
        `AsyncConverter().async_convert_iterable()` with
        both an empty input.
        """

        mock_converter = create_autospec(AsyncConverter, spec_set=True)

        observed = await AsyncConverter.async_convert_iterable(
            mock_converter,
            (i for i in [])
        )

        assert list(observed) == []

    async def test_async_convert_iterable_populated(self):
        """
        `AsyncConverter().async_convert_iterable()` with
        both empty and mixed (`None` and populated) inputs.
        """

        input_ = [
            i if i % 2 == 0 else None
            for i in range(5)
        ]

        expected_calls = [call(i) for i in input_]

        pass_ = iter(
            [
                i + 1 if i is not None else None
                for i in input_
            ]
        )

        mock_converter = create_autospec(AsyncConverter, spec_set=True)
        mock_converter.async_convert_optional.side_effect = lambda _: next(pass_)

        observed = await AsyncConverter.async_convert_iterable(
            mock_converter,
            input_
        )

        assert mock_converter.async_convert_optional.call_args_list == (
            expected_calls
        )
        assert list(observed) == [1, None, 3, None, 5]
