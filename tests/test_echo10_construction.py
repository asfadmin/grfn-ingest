import main


def test_write_to_file(tmp_path):
    target = tmp_path / 'foo.txt'
    main.write_to_file(str(target), 'hello world')
    assert target.exists()
    assert target.read_text() == 'hello world'
