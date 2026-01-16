"""Selectors (CSS/XPath) for pages."""

# Login page
USERNAME_INPUT = "#usernameInput"
PASSWORD_INPUT = "#passwordInput"
LOGIN_BUTTON = "#loginButton"

# License page
LICENSE_CHECKBOX = "#agreementCheckBox"

# Navigation
INVENTORY_LINK = "a[href='/ValuesOnline/vehicle/']"

# Inventory page
GRID_TABLE = "table"  # TODO: Update with actual selector
STOCK_NUMBER_INPUT = "#StockNumberInput"
BOOKOUT_LINK = "a[id^='bookOutButton_'][title='Bookout']"  # Bookout link by ID pattern
BOOKOUT_IMAGE = "img[title='Bookout'][src*='book.png']"  # Alternative: find by image
CLEAR_FILTERS_BUTTON = "a.dxgvFilterBarLink[onclick*='ClearFilter']"
CREATE_FILTER_BUTTON = "a.dxgvFilterBarLink[onclick*='ShowFilterControl']"

# CSV Export menu
EXPORT_MENU_BUTTON = "#primaryMenu_DXI4_T"  # Export button with icon
EXPORT_ALL_COLUMNS = "#primaryMenu_DXI4i1_T"  # Export All Columns submenu
EXPORT_TO_CSV = "#primaryMenu_DXI4i1i2_"  # Export to CSV option

# Vehicle page
PRINT_EMAIL_BUTTON = "button.reportButton:not(.requiresVehicle)"  # Print/Email Reports button (not the requiresVehicle one)
CREATE_PDF_BUTTON = "button:has-text('Create PDF')"  # Create PDF button in modal

# Logout
LOGOUT_BUTTON = "#btnLogout"

