import pytest
from csv_controller import save_to_csv, read_from_csv, remove_from_csv
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

def test_read_from_csv():
    mock_csv_data = "Tisch,192.168.0.38"

    # ✅ Mock the open() function
    with patch("builtins.open", mock_open(read_data=mock_csv_data)) as mock_file:
        result = read_from_csv()  # Fake filename, but mocked

    assert result == [("Tisch", "192.168.0.38")]

def test_read_from_csv_multiple():
    mock_csv_data = "Tisch,192.168.0.38\nSofa,192.168.0.39\nlampe,192.168.0.200"

    # ✅ Mock the open() function
    with patch("builtins.open", mock_open(read_data=mock_csv_data)) as mock_file:
        result = read_from_csv()  # Fake filename, but mocked

    assert result == [("Tisch", "192.168.0.38"),("Sofa", "192.168.0.39"),("lampe", "192.168.0.200")]

def test_read_from_csv_empty():
    mock_csv_data = ""

    # ✅ Mock the open() function
    with patch("builtins.open", mock_open(read_data=mock_csv_data)) as mock_file:
        result = read_from_csv()  # Fake filename, but mocked

    assert result == []


@patch("csv_controller.read_from_csv")  # ✅ Mock the read_from_csv function
@patch("builtins.open", new_callable=mock_open)  # ✅ Mock file writing
def test_remove_from_csv(mock_file, mock_read_from_csv):
    # ✅ Mock CSV data before deletion
    mock_read_from_csv.return_value = [
        ["Tisch", "192.168.0.38"],
        ["Lamp", "192.168.0.40"]
    ]

    # ✅ Call function (removing "192.168.0.38")
    result = remove_from_csv("192.168.0.38")

    # ✅ Ensure function returns True
    assert result is True

    # ✅ Capture what was written back to the file
    mock_file_handle = mock_file()
    written_data = "".join(call.args[0] for call in mock_file_handle.write.call_args_list)

    # ✅ Expected remaining data (after removing 192.168.0.38)
    expected_remaining_data = "Lamp,192.168.0.40\n"

    # ✅ Verify that "192.168.0.38" is not in the output
    assert "192.168.0.38" not in written_data
    assert written_data.strip() == expected_remaining_data.strip()


@patch("csv_controller.read_from_csv")  # ✅ Mock the read_from_csv function
@patch("builtins.open", new_callable=mock_open)  # ✅ Mock file writing
def test_remove_from_csv_wrong(mock_file, mock_read_from_csv):
    # ✅ Mock CSV data before deletion
    mock_read_from_csv.return_value = [
        ["Tisch", "192.168.0.38"],
        ["Lamp", "192.168.0.40"]
    ]

    # ✅ Call function (removing "192.168.0.34")
    result = remove_from_csv("192.168.0.34")

    # ✅ Ensure function returns True
    assert result is False
    mock_file_handle = mock_file()
    mock_file_handle.write.assert_not_called()


@patch("csv_controller.read_from_csv")  # ✅ Mock the read_from_csv function
@patch("builtins.open", new_callable=mock_open)  # ✅ Mock file writing
def test_remove_from_csv_to_empty(mock_file, mock_read_from_csv):
    # ✅ Mock CSV data before deletion
    mock_read_from_csv.return_value = [
        ["Tisch", "192.168.0.38"]
    ]

    # ✅ Call function (removing "192.168.0.38")
    result = remove_from_csv("192.168.0.38")

    # ✅ Ensure function returns True
    assert result is True

    # ✅ Capture what was written back to the file
    mock_file_handle = mock_file()
    written_data = "".join(call.args[0] for call in mock_file_handle.write.call_args_list)

    # ✅ Expected remaining data (after removing 192.168.0.38)
    expected_remaining_data = ""

    assert written_data.strip() == expected_remaining_data.strip()


@patch("csv_controller.read_from_csv")  # ✅ Mock the read_from_csv function
@patch("builtins.open", new_callable=mock_open)  # ✅ Mock file writing
def test_remove_from_csv_multiple_with_same_ip(mock_file, mock_read_from_csv):
    # ✅ Mock CSV data before deletion
    mock_read_from_csv.return_value = [
        ["Tisch", "192.168.0.38"],
        ["Panda", "192.168.0.38"],
        ["Tiger", "192.168.0.38"],
        ["Fisch", "192.168.0.33"]
    ]

    # ✅ Call function (removing "192.168.0.38")
    result = remove_from_csv("192.168.0.38")

    # ✅ Ensure function returns True
    assert result is True

    # ✅ Capture what was written back to the file
    mock_file_handle = mock_file()
    written_data = "".join(call.args[0] for call in mock_file_handle.write.call_args_list)

    # ✅ Expected remaining data (after removing 192.168.0.38)
    expected_remaining_data = "Fisch,192.168.0.33\n"

    assert written_data.strip() == expected_remaining_data.strip()

