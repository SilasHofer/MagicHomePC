import pytest
from csv_controller import save_to_csv
from unittest.mock import patch, mock_open

@patch("builtins.open", new_callable=mock_open)
def test_save_to_csv(mock_file):
    result = save_to_csv("Test", "192.168.10.123")
    assert result == True
    mock_file.assert_called_once_with("devices.csv", "a", newline="")
    mock_file_handle = mock_file()
    written_data = mock_file_handle.write.call_args_list

    expected_data = "Test,192.168.10.123"
    assert any(expected_data in str(call) for call in written_data)


@patch("builtins.open", new_callable=mock_open)
def test_save_to_csv_multiple(mock_file):
    result1 = save_to_csv("Test", "192.168.10.123")
    result2 = save_to_csv("Test2", "192.168.10.200")

    assert result1 == True
    assert result2 == True

    assert mock_file.call_count == 2  # Check total number of calls

    mock_file_handle = mock_file()
    # ✅ Extract all write calls as a list of written strings
    written_data = [call.args[0].strip() for call in mock_file_handle.write.call_args_list]

    # ✅ Ensure expected data is written
    expected_data = ["Test,192.168.10.123","Test2,192.168.10.200"]  # CSV writer adds newline

    assert written_data == expected_data, f"Expected {expected_data} but got {written_data}"


