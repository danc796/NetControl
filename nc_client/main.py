from nc_client.ui.main_window import MainWindow
from nc_client.utils.logging import setup_logging


def main():
    # Setup logging first - only needs to be done once
    setup_logging()

    # Then initialize the main window
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()