from unittest.mock import patch

import main


def test_run_app_uses_positional_main_callback():
    with patch("main.ft.run") as mock_run:
        main.run_app()

    assert mock_run.call_count == 1
    assert mock_run.call_args.args == (main.main,)
    assert mock_run.call_args.kwargs == {}
