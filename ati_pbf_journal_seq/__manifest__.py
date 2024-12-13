{
    "name": "ATI PBF - JOURNAL SEQUENCE",
    "version": "15.0.1.0",
    "author": "ATI",
    "category": "Invoice",
    "summary": "Set Journal Sequence",
    "description": """

    """,
    "depends": [
        'account',
    ],
    "data": [
        'data/ir_sequence.xml',
        'views/account_journal.xml',
        'views/account_move.xml',
    ],
    "qweb": [],
    "image": [],
    "installable": True,
    "application": False,
    "auto_install": False,
}