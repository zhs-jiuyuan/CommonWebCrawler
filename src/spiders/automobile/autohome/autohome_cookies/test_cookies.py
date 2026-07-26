import sys
from unittest.mock import MagicMock

sys.path.insert(0, "src/spiders/automobile/autohome")

from autohome_cookies import _locate_button, _click_find_car


class TestLocateButton:
    def test_locates_by_xpath_first(self):
        mock_page = MagicMock()
        mock_locator = MagicMock()
        mock_locator.count.return_value = 1
        mock_page.locator.return_value = mock_locator

        result = _locate_button(mock_page)

        assert result is mock_locator.first
        mock_page.locator.assert_called_with(
            'xpath=//*[@id="app"]/div[1]/div[2]/section[2]/div[1]/div[2]/div/div[1]/a'
        )

    def test_falls_back_to_text_when_xpath_empty(self):
        mock_page = MagicMock()
        xpath_loc = MagicMock()
        xpath_loc.count.return_value = 0
        text_loc = MagicMock()
        text_loc.count.return_value = 1
        mock_page.locator.side_effect = [xpath_loc, text_loc]

        result = _locate_button(mock_page)

        assert result is text_loc.first
        assert mock_page.locator.call_count == 2

    def test_falls_back_to_class_when_two_empty(self):
        mock_page = MagicMock()
        empty = MagicMock()
        empty.count.return_value = 0
        class_loc = MagicMock()
        class_loc.count.return_value = 1
        mock_page.locator.side_effect = [empty, empty, class_loc]

        result = _locate_button(mock_page)

        assert result is class_loc.first
        assert mock_page.locator.call_count == 3

    def test_raises_when_all_empty(self):
        mock_page = MagicMock()
        empty = MagicMock()
        empty.count.return_value = 0
        mock_page.locator.return_value = empty

        try:
            _locate_button(mock_page)
            assert False, "should have raised"
        except RuntimeError as e:
            assert "找不到" in str(e)


class TestClickFindCar:
    def test_clicks_and_returns_none(self):
        mock_page = MagicMock()
        mock_context = MagicMock()
        mock_event_info = MagicMock()
        mock_new_page = MagicMock()
        mock_event_info.value = mock_new_page
        mock_context.expect_page.return_value.__enter__.return_value = mock_event_info

        mock_btn = MagicMock()
        mock_page.locator.return_value = mock_btn
        mock_btn.count.return_value = 1
        mock_btn.first = mock_btn

        result = _click_find_car(mock_page, mock_context, 30000)

        mock_btn.click.assert_called_once()
        mock_new_page.wait_for_load_state.assert_called_once_with('networkidle')
        assert result is None
