from datetime import date

FAKE_DATA = {
    'fake_accounts': [
        dict(
        name='AnyBank Checking',
        debit_positive = True,
        date_format = "%m/%d/%Y",
        credit_map = "Credit",
        debit_map = "Debit",
        description_map = "Description",
        date_map = "Date"
        ),
        dict(
        name='AnyCard ',
        debit_positive = True,
        date_format = "%m/%d/%Y",
        credit_map = "Credit",
        debit_map = "Debit",
        description_map = "Description",
        date_map = "Date"
        ),
    ],
    'fake_categories': [
        dict(name='Income'),
        dict(name='Groceries'),
        dict(name='Utilities'),
        dict(name='Automotive'),
        dict(name='Media/Entertainment'),
        dict(name='Restaurants'),
        dict(name='Business Expense'),
        dict(name='Rent'),
    ],
    'fake_transactions': [
        dict(
            account_id=2,
            date=date(year=2020, month=7, day=2),
            description='COSTCO WHOLESALE',
            category_id=2,
            amount=-222.62,
        ),
        dict(
            account_id=1,
            date=date(year=2020, month=7, day=7),
            description='Monopoly Cable Corp',
            category_id=3,
            amount=-95.62,
        ),
        dict(
            account_id=2,
            date=date(year=2020, month=7, day=8),
            description='DINO JUICE LLC',
            category_id=4,
            amount=-35.24,
        ),
        dict(
            account_id=2,
            date=date(year=2020, month=7, day=8),
            description='Netflix',
            category_id=5,
            amount=-16.99,
        ),
        dict(
            account_id=1,
            date=date(year=2020, month=7, day=2),
            description='Software Shack LLC',
            category_id=1,
            amount=2509.78,
        ),
        dict(
            account_id=1,
            date=date(year=2020, month=7, day=10),
            description='COSTCO WHOLESALE',
            category_id=1,
            amount=-101.32,
        ),
        dict(
            account_id=1,
            date=date(year=2020, month=7, day=12),
            description='Sushi That Goes Around On A Belt',
            category_id=6,
            amount=-15.75,
        ),
        dict(
            account_id=1,
            date=date(year=2020, month=7, day=15),
            description='DELL COMPUTERS INC.',
            category_id=7,
            amount=-765.74,
        ),
        dict(
            account_id=2,
            date=date(year=2020, month=7, day=20),
            description='Royal India Cuisine',
            category_id=6,
            amount=-54.39,
        ),
        dict(
            account_id=1,
            date=date(year=2020, month=7, day=18),
            description='Check Cashed #768',
            category_id=3,
            amount=-85.95,
        ),
        dict(
            account_id=2,
            date=date(year=2020, month=7, day=11),
            description='GROCERY MART',
            category_id=2,
            amount=-42.55,
        ),
        dict(
            account_id=1,
            date=date(year=2020, month=7, day=22),
            description='SPOTIFY S.A.',
            category_id=5,
            amount=-9.99,
        ),
        dict(
            account_id=2,
            date=date(year=2020, month=7, day=2),
            description='Chip Shop',
            category_id=6,
            amount=-11.88,
        ),
        dict(
            account_id=1,
            date=date(year=2020, month=7, day=31),
            description='Rent',
            category_id=8,
            amount=-850.00,
        ),
        dict(
            account_id=1,
            date=date(year=2020, month=7, day=16),
            description='WAKEMUP GARBAGE SERVICE, LLC',
            category_id=3,
            amount=-24.18,
        ),

    ]

}

