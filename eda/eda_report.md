# Starbucks Dataset Exploratory Data Analysis

## Scope

This EDA profiles the raw Starbucks Rewards files before treatment/outcome reconstruction. It is descriptive only; it does not yet create the leakage-free modeling table.

## Dataset inventory

| File | Rows | Purpose |
| --- | --- | --- |
| portfolio.json | 10 | Offer metadata |
| profile.json | 17000 | Customer demographics |
| transcript.json | 306534 | Timestamped customer events |

## Portfolio findings

| Offer type | Count |
| --- | --- |
| bogo | 4 |
| discount | 4 |
| informational | 2 |

Channels: email (10), mobile (9), web (8), social (6).


## Profile findings

| Field | Missing | Missing rate |
| --- | --- | --- |
| age | 0 | 0.00% |
| became_member_on | 0 | 0.00% |
| gender | 2175 | 12.79% |
| id | 0 | 0.00% |
| income | 2175 | 12.79% |

Gender distribution: M (8484), F (6129), None (2175), O (212).

Income distribution: None (2175), 73000 (314), 72000 (297), 71000 (294), 57000 (288), 53000 (282), 74000 (282), 52000 (281), 56000 (281), 54000 (272), 70000 (270), 51000 (268), 64000 (258), 61000 (258), 55000 (254), 50000 (253), 60000 (251), 59000 (243), 75000 (243), 67000 (242), 58000 (239), 65000 (238), 62000 (229), 68000 (228), 31000 (223), 66000 (222), 32000 (216), 33000 (213), 37000 (209), 39000 (209), 63000 (206), 35000 (206), 41000 (204), 34000 (199), 69000 (196), 45000 (196), 40000 (195), 47000 (192), 36000 (192), 48000 (186), 38000 (185), 46000 (181), 42000 (181), 44000 (180), 43000 (169), 79000 (166), 77000 (158), 76000 (157), 49000 (157), 78000 (157), 80000 (152), 87000 (151), 84000 (148), 81000 (147), 88000 (146), 85000 (145), 92000 (140), 89000 (137), 96000 (132), 93000 (132), 83000 (129), 86000 (128), 82000 (126), 95000 (126), 97000 (124), 99000 (123), 90000 (114), 98000 (112), 91000 (106), 94000 (106), 30000 (88), 100000 (87), 109000 (62), 103000 (59), 105000 (58), 118000 (58), 110000 (58), 108000 (57), 106000 (56), 104000 (55), 111000 (55), 119000 (54), 113000 (54), 114000 (53), 115000 (50), 101000 (48), 102000 (48), 116000 (46), 112000 (45), 107000 (45), 117000 (32), 120000 (13).

Age excluding the dataset sentinel value 118: min=18, max=101, mean=54.4. The value 118 occurs 2175 times and should be treated as missing.


## Transcript findings

| Event | Count | Share |
| --- | --- | --- |
| transaction | 138953 | 45.33% |
| offer received | 76277 | 24.88% |
| offer viewed | 57725 | 18.83% |
| offer completed | 33579 | 10.95% |

Event payload keys: amount (138953), offer id (134002), offer_id (33579), reward (33579).

Unique customers in transcript: 17000. Events per customer: min=1, max=51, mean=18.0.

Timestamp range in hours since study start: 0 to 714.

Transactions: 138953; offer views: 57725; offer receipts: 76277; offer completions: 33579.

Transaction amount: min=0.05, max=1062.28, mean=12.78.
