import datetime

CAREER_RANKS = {
    # NOTE: There is no rank #-1, but this kludge allows relative math to work.
    -1: {"name": "Kludge", "cumulative_score": 0},
    0: {"name": "Recruit", "cumulative_score": 100},
    1: {"name": "Cadet Bronze (Tier 1)", "cumulative_score": 1100},
    2: {"name": "Cadet Bronze (Tier 2)", "cumulative_score": 2350},
    3: {"name": "Cadet Bronze (Tier 3)", "cumulative_score": 3850},
    4: {"name": "Private Bronze (Tier 1)", "cumulative_score": 4850},
    5: {"name": "Private Bronze (Tier 2)", "cumulative_score": 6100},
    6: {"name": "Private Bronze (Tier 3)", "cumulative_score": 7850},
    7: {"name": "Lance Corporal Bronze (Tier 1)", "cumulative_score": 9100},
    8: {"name": "Lance Corporal Bronze (Tier 2)", "cumulative_score": 10600},
    9: {"name": "Lance Corporal Bronze (Tier 3)", "cumulative_score": 12350},
    10: {"name": "Corporal Bronze (Tier 1)", "cumulative_score": 13600},
    11: {"name": "Corporal Bronze (Tier 2)", "cumulative_score": 15100},
    12: {"name": "Corporal Bronze (Tier 3)", "cumulative_score": 17100},
    13: {"name": "Sergeant Bronze (Tier 1)", "cumulative_score": 18600},
    14: {"name": "Sergeant Bronze (Tier 2)", "cumulative_score": 20350},
    15: {"name": "Sergeant Bronze (Tier 3)", "cumulative_score": 22600},
    16: {"name": "Staff Sergeant Bronze (Tier 1)", "cumulative_score": 24100},
    17: {"name": "Staff Sergeant Bronze (Tier 2)", "cumulative_score": 25850},
    18: {"name": "Staff Sergeant Bronze (Tier 3)", "cumulative_score": 28350},
    19: {"name": "Gunnery Sergeant Bronze (Tier 1)", "cumulative_score": 30100},
    20: {"name": "Gunnery Sergeant Bronze (Tier 2)", "cumulative_score": 32100},
    21: {"name": "Gunnery Sergeant Bronze (Tier 3)", "cumulative_score": 34850},
    22: {"name": "Master Sergeant Bronze (Tier 1)", "cumulative_score": 36600},
    23: {"name": "Master Sergeant Bronze (Tier 2)", "cumulative_score": 38850},
    24: {"name": "Master Sergeant Bronze (Tier 3)", "cumulative_score": 41850},
    25: {"name": "Lieutenant Bronze (Tier 1)", "cumulative_score": 43850},
    26: {"name": "Lieutenant Bronze (Tier 2)", "cumulative_score": 46350},
    27: {"name": "Lieutenant Bronze (Tier 3)", "cumulative_score": 49600},
    28: {"name": "Captain Bronze (Tier 1)", "cumulative_score": 51850},
    29: {"name": "Captain Bronze (Tier 2)", "cumulative_score": 54600},
    30: {"name": "Captain Bronze (Tier 3)", "cumulative_score": 58100},
    31: {"name": "Major Bronze (Tier 1)", "cumulative_score": 60600},
    32: {"name": "Major Bronze (Tier 2)", "cumulative_score": 63600},
    33: {"name": "Major Bronze (Tier 3)", "cumulative_score": 67350},
    34: {"name": "Lt Colonel Bronze (Tier 1)", "cumulative_score": 70100},
    35: {"name": "Lt Colonel Bronze (Tier 2)", "cumulative_score": 73350},
    36: {"name": "Lt Colonel Bronze (Tier 3)", "cumulative_score": 77350},
    37: {"name": "Colonel Bronze (Tier 1)", "cumulative_score": 80350},
    38: {"name": "Colonel Bronze (Tier 2)", "cumulative_score": 83850},
    39: {"name": "Colonel Bronze (Tier 3)", "cumulative_score": 88350},
    40: {"name": "Brigadier General Bronze (Tier 1)", "cumulative_score": 91600},
    41: {"name": "Brigadier General Bronze (Tier 2)", "cumulative_score": 95350},
    42: {"name": "Brigadier General Bronze (Tier 3)", "cumulative_score": 100350},
    43: {"name": "General Bronze (Tier 1)", "cumulative_score": 103850},
    44: {"name": "General Bronze (Tier 2)", "cumulative_score": 107850},
    45: {"name": "General Bronze (Tier 3)", "cumulative_score": 113100},
    46: {"name": "Cadet Silver (Tier 1)", "cumulative_score": 115350},
    47: {"name": "Cadet Silver (Tier 2)", "cumulative_score": 117850},
    48: {"name": "Cadet Silver (Tier 3)", "cumulative_score": 121100},
    49: {"name": "Private Silver (Tier 1)", "cumulative_score": 123350},
    50: {"name": "Private Silver (Tier 2)", "cumulative_score": 126100},
    51: {"name": "Private Silver (Tier 3)", "cumulative_score": 129850},
    52: {"name": "Lance Corporal Silver (Tier 1)", "cumulative_score": 132350},
    53: {"name": "Lance Corporal Silver (Tier 2)", "cumulative_score": 135350},
    54: {"name": "Lance Corporal Silver (Tier 3)", "cumulative_score": 139350},
    55: {"name": "Corporal Silver (Tier 1)", "cumulative_score": 142100},
    56: {"name": "Corporal Silver (Tier 2)", "cumulative_score": 145350},
    57: {"name": "Corporal Silver (Tier 3)", "cumulative_score": 149600},
    58: {"name": "Sergeant Silver (Tier 1)", "cumulative_score": 152600},
    59: {"name": "Sergeant Silver (Tier 2)", "cumulative_score": 156350},
    60: {"name": "Sergeant Silver (Tier 3)", "cumulative_score": 161100},
    61: {"name": "Staff Sergeant Silver (Tier 1)", "cumulative_score": 164350},
    62: {"name": "Staff Sergeant Silver (Tier 2)", "cumulative_score": 168350},
    63: {"name": "Staff Sergeant Silver (Tier 3)", "cumulative_score": 173600},
    64: {"name": "Gunnery Sergeant Silver (Tier 1)", "cumulative_score": 177350},
    65: {"name": "Gunnery Sergeant Silver (Tier 2)", "cumulative_score": 181600},
    66: {"name": "Gunnery Sergeant Silver (Tier 3)", "cumulative_score": 187350},
    67: {"name": "Master Sergeant Silver (Tier 1)", "cumulative_score": 191350},
    68: {"name": "Master Sergeant Silver (Tier 2)", "cumulative_score": 196100},
    69: {"name": "Master Sergeant Silver (Tier 3)", "cumulative_score": 202350},
    70: {"name": "Lieutenant Silver (Tier 1)", "cumulative_score": 206600},
    71: {"name": "Lieutenant Silver (Tier 2)", "cumulative_score": 211850},
    72: {"name": "Lieutenant Silver (Tier 3)", "cumulative_score": 218600},
    73: {"name": "Captain Silver (Tier 1)", "cumulative_score": 223350},
    74: {"name": "Captain Silver (Tier 2)", "cumulative_score": 229100},
    75: {"name": "Captain Silver (Tier 3)", "cumulative_score": 236350},
    76: {"name": "Major Silver (Tier 1)", "cumulative_score": 241600},
    77: {"name": "Major Silver (Tier 2)", "cumulative_score": 247850},
    78: {"name": "Major Silver (Tier 3)", "cumulative_score": 255850},
    79: {"name": "Lt Colonel Silver (Tier 1)", "cumulative_score": 261600},
    80: {"name": "Lt Colonel Silver (Tier 2)", "cumulative_score": 268350},
    81: {"name": "Lt Colonel Silver (Tier 3)", "cumulative_score": 277100},
    82: {"name": "Colonel Silver (Tier 1)", "cumulative_score": 283350},
    83: {"name": "Colonel Silver (Tier 2)", "cumulative_score": 290850},
    84: {"name": "Colonel Silver (Tier 3)", "cumulative_score": 300350},
    85: {"name": "Brigadier General Silver (Tier 1)", "cumulative_score": 307100},
    86: {"name": "Brigadier General Silver (Tier 2)", "cumulative_score": 315100},
    87: {"name": "Brigadier General Silver (Tier 3)", "cumulative_score": 325100},
    88: {"name": "General Silver (Tier 1)", "cumulative_score": 332350},
    89: {"name": "General Silver (Tier 2)", "cumulative_score": 341100},
    90: {"name": "General Silver (Tier 3)", "cumulative_score": 353600},
    91: {"name": "Cadet Gold (Tier 1)", "cumulative_score": 358100},
    92: {"name": "Cadet Gold (Tier 2)", "cumulative_score": 363600},
    93: {"name": "Cadet Gold (Tier 3)", "cumulative_score": 370850},
    94: {"name": "Private Gold (Tier 1)", "cumulative_score": 375850},
    95: {"name": "Private Gold (Tier 2)", "cumulative_score": 381850},
    96: {"name": "Private Gold (Tier 3)", "cumulative_score": 389600},
    97: {"name": "Lance Corporal Gold (Tier 1)", "cumulative_score": 395100},
    98: {"name": "Lance Corporal Gold (Tier 2)", "cumulative_score": 401600},
    99: {"name": "Lance Corporal Gold (Tier 3)", "cumulative_score": 410100},
    100: {"name": "Corporal Gold (Tier 1)", "cumulative_score": 416100},
    101: {"name": "Corporal Gold (Tier 2)", "cumulative_score": 423350},
    102: {"name": "Corporal Gold (Tier 3)", "cumulative_score": 432600},
    103: {"name": "Sergeant Gold (Tier 1)", "cumulative_score": 439100},
    104: {"name": "Sergeant Gold (Tier 2)", "cumulative_score": 446850},
    105: {"name": "Sergeant Gold (Tier 3)", "cumulative_score": 456850},
    106: {"name": "Staff Sergeant Gold (Tier 1)", "cumulative_score": 463850},
    107: {"name": "Staff Sergeant Gold (Tier 2)", "cumulative_score": 472350},
    108: {"name": "Staff Sergeant Gold (Tier 3)", "cumulative_score": 482350},
    109: {"name": "Gunnery Sergeant Gold (Tier 1)", "cumulative_score": 490100},
    110: {"name": "Gunnery Sergeant Gold (Tier 2)", "cumulative_score": 499350},
    111: {"name": "Gunnery Sergeant Gold (Tier 3)", "cumulative_score": 511850},
    112: {"name": "Master Sergeant Gold (Tier 1)", "cumulative_score": 520350},
    113: {"name": "Master Sergeant Gold (Tier 2)", "cumulative_score": 530350},
    114: {"name": "Master Sergeant Gold (Tier 3)", "cumulative_score": 542850},
    115: {"name": "Lieutenant Gold (Tier 1)", "cumulative_score": 552100},
    116: {"name": "Lieutenant Gold (Tier 2)", "cumulative_score": 562100},
    117: {"name": "Lieutenant Gold (Tier 3)", "cumulative_score": 577100},
    118: {"name": "Captain Gold (Tier 1)", "cumulative_score": 587100},
    119: {"name": "Captain Gold (Tier 2)", "cumulative_score": 599600},
    120: {"name": "Captain Gold (Tier 3)", "cumulative_score": 614600},
    121: {"name": "Major Gold (Tier 1)", "cumulative_score": 624600},
    122: {"name": "Major Gold (Tier 2)", "cumulative_score": 637100},
    123: {"name": "Major Gold (Tier 3)", "cumulative_score": 654600},
    124: {"name": "Lt Colonel Gold (Tier 1)", "cumulative_score": 667100},
    125: {"name": "Lt Colonel Gold (Tier 2)", "cumulative_score": 682100},
    126: {"name": "Lt Colonel Gold (Tier 3)", "cumulative_score": 702100},
    127: {"name": "Colonel Gold (Tier 1)", "cumulative_score": 714600},
    128: {"name": "Colonel Gold (Tier 2)", "cumulative_score": 729600},
    129: {"name": "Colonel Gold (Tier 3)", "cumulative_score": 749600},
    130: {"name": "Brigadier General Gold (Tier 1)", "cumulative_score": 764600},
    131: {"name": "Brigadier General Gold (Tier 2)", "cumulative_score": 782100},
    132: {"name": "Brigadier General Gold (Tier 3)", "cumulative_score": 804600},
    133: {"name": "General Gold (Tier 1)", "cumulative_score": 819600},
    134: {"name": "General Gold (Tier 2)", "cumulative_score": 839600},
    135: {"name": "General Gold (Tier 3)", "cumulative_score": 864600},
    136: {"name": "Cadet Platinum (Tier 1)", "cumulative_score": 874350},
    137: {"name": "Cadet Platinum (Tier 2)", "cumulative_score": 886850},
    138: {"name": "Cadet Platinum (Tier 3)", "cumulative_score": 901850},
    139: {"name": "Private Platinum (Tier 1)", "cumulative_score": 911850},
    140: {"name": "Private Platinum (Tier 2)", "cumulative_score": 924350},
    141: {"name": "Private Platinum (Tier 3)", "cumulative_score": 941850},
    142: {"name": "Lance Corporal Platinum (Tier 1)", "cumulative_score": 954350},
    143: {"name": "Lance Corporal Platinum (Tier 2)", "cumulative_score": 969350},
    144: {"name": "Lance Corporal Platinum (Tier 3)", "cumulative_score": 986850},
    145: {"name": "Corporal Platinum (Tier 1)", "cumulative_score": 999350},
    146: {"name": "Corporal Platinum (Tier 2)", "cumulative_score": 1014350},
    147: {"name": "Corporal Platinum (Tier 3)", "cumulative_score": 1034350},
    148: {"name": "Sergeant Platinum (Tier 1)", "cumulative_score": 1049350},
    149: {"name": "Sergeant Platinum (Tier 2)", "cumulative_score": 1066850},
    150: {"name": "Sergeant Platinum (Tier 3)", "cumulative_score": 1089350},
    151: {"name": "Staff Sergeant Platinum (Tier 1)", "cumulative_score": 1104350},
    152: {"name": "Staff Sergeant Platinum (Tier 2)", "cumulative_score": 1121850},
    153: {"name": "Staff Sergeant Platinum (Tier 3)", "cumulative_score": 1144350},
    154: {"name": "Gunnery Sergeant Platinum (Tier 1)", "cumulative_score": 1161850},
    155: {"name": "Gunnery Sergeant Platinum (Tier 2)", "cumulative_score": 1181850},
    156: {"name": "Gunnery Sergeant Platinum (Tier 3)", "cumulative_score": 1206850},
    157: {"name": "Master Sergeant Platinum (Tier 1)", "cumulative_score": 1224350},
    158: {"name": "Master Sergeant Platinum (Tier 2)", "cumulative_score": 1246850},
    159: {"name": "Master Sergeant Platinum (Tier 3)", "cumulative_score": 1274350},
    160: {"name": "Lieutenant Platinum (Tier 1)", "cumulative_score": 1294350},
    161: {"name": "Lieutenant Platinum (Tier 2)", "cumulative_score": 1319350},
    162: {"name": "Lieutenant Platinum (Tier 3)", "cumulative_score": 1349350},
    163: {"name": "Captain Platinum (Tier 1)", "cumulative_score": 1371850},
    164: {"name": "Captain Platinum (Tier 2)", "cumulative_score": 1396850},
    165: {"name": "Captain Platinum (Tier 3)", "cumulative_score": 1429350},
    166: {"name": "Major Platinum (Tier 1)", "cumulative_score": 1451850},
    167: {"name": "Major Platinum (Tier 2)", "cumulative_score": 1479350},
    168: {"name": "Major Platinum (Tier 3)", "cumulative_score": 1516850},
    169: {"name": "Lt Colonel Platinum (Tier 1)", "cumulative_score": 1541850},
    170: {"name": "Lt Colonel Platinum (Tier 2)", "cumulative_score": 1571850},
    171: {"name": "Lt Colonel Platinum (Tier 3)", "cumulative_score": 1611850},
    172: {"name": "Colonel Platinum (Tier 1)", "cumulative_score": 1639350},
    173: {"name": "Colonel Platinum (Tier 2)", "cumulative_score": 1674350},
    174: {"name": "Colonel Platinum (Tier 3)", "cumulative_score": 1719350},
    175: {"name": "Brigadier General Platinum (Tier 1)", "cumulative_score": 1749350},
    176: {"name": "Brigadier General Platinum (Tier 2)", "cumulative_score": 1786850},
    177: {"name": "Brigadier General Platinum (Tier 3)", "cumulative_score": 1834350},
    178: {"name": "General Platinum (Tier 1)", "cumulative_score": 1866850},
    179: {"name": "General Platinum (Tier 2)", "cumulative_score": 1906850},
    180: {"name": "General Platinum (Tier 3)", "cumulative_score": 1959350},
    181: {"name": "Cadet Diamond (Tier 1)", "cumulative_score": 1979350},
    182: {"name": "Cadet Diamond (Tier 2)", "cumulative_score": 2004350},
    183: {"name": "Cadet Diamond (Tier 3)", "cumulative_score": 2036850},
    184: {"name": "Private Diamond (Tier 1)", "cumulative_score": 2059350},
    185: {"name": "Private Diamond (Tier 2)", "cumulative_score": 2086850},
    186: {"name": "Private Diamond (Tier 3)", "cumulative_score": 2121850},
    187: {"name": "Lance Corporal Diamond (Tier 1)", "cumulative_score": 2146850},
    188: {"name": "Lance Corporal Diamond (Tier 2)", "cumulative_score": 2176850},
    189: {"name": "Lance Corporal Diamond (Tier 3)", "cumulative_score": 2216850},
    190: {"name": "Corporal Diamond (Tier 1)", "cumulative_score": 2244350},
    191: {"name": "Corporal Diamond (Tier 2)", "cumulative_score": 2276850},
    192: {"name": "Corporal Diamond (Tier 3)", "cumulative_score": 2319350},
    193: {"name": "Sergeant Diamond (Tier 1)", "cumulative_score": 2349350},
    194: {"name": "Sergeant Diamond (Tier 2)", "cumulative_score": 2384350},
    195: {"name": "Sergeant Diamond (Tier 3)", "cumulative_score": 2431850},
    196: {"name": "Staff Sergeant Diamond (Tier 1)", "cumulative_score": 2464350},
    197: {"name": "Staff Sergeant Diamond (Tier 2)", "cumulative_score": 2504350},
    198: {"name": "Staff Sergeant Diamond (Tier 3)", "cumulative_score": 2554350},
    199: {"name": "Gunnery Sergeant Diamond (Tier 1)", "cumulative_score": 2589350},
    200: {"name": "Gunnery Sergeant Diamond (Tier 2)", "cumulative_score": 2631850},
    201: {"name": "Gunnery Sergeant Diamond (Tier 3)", "cumulative_score": 2686850},
    202: {"name": "Master Sergeant Diamond (Tier 1)", "cumulative_score": 2726850},
    203: {"name": "Master Sergeant Diamond (Tier 2)", "cumulative_score": 2774350},
    204: {"name": "Master Sergeant Diamond (Tier 3)", "cumulative_score": 2834350},
    205: {"name": "Lieutenant Diamond (Tier 1)", "cumulative_score": 2876850},
    206: {"name": "Lieutenant Diamond (Tier 2)", "cumulative_score": 2926850},
    207: {"name": "Lieutenant Diamond (Tier 3)", "cumulative_score": 2991850},
    208: {"name": "Captain Diamond (Tier 1)", "cumulative_score": 3039350},
    209: {"name": "Captain Diamond (Tier 2)", "cumulative_score": 3094350},
    210: {"name": "Captain Diamond (Tier 3)", "cumulative_score": 3166850},
    211: {"name": "Major Diamond (Tier 1)", "cumulative_score": 3216850},
    212: {"name": "Major Diamond (Tier 2)", "cumulative_score": 3276850},
    213: {"name": "Major Diamond (Tier 3)", "cumulative_score": 3356850},
    214: {"name": "Lt Colonel Diamond (Tier 1)", "cumulative_score": 3411850},
    215: {"name": "Lt Colonel Diamond (Tier 2)", "cumulative_score": 3476850},
    216: {"name": "Lt Colonel Diamond (Tier 3)", "cumulative_score": 3561850},
    217: {"name": "Colonel Diamond (Tier 1)", "cumulative_score": 3621850},
    218: {"name": "Colonel Diamond (Tier 2)", "cumulative_score": 3694350},
    219: {"name": "Colonel Diamond (Tier 3)", "cumulative_score": 3789350},
    220: {"name": "Brigadier General Diamond (Tier 1)", "cumulative_score": 3854350},
    221: {"name": "Brigadier General Diamond (Tier 2)", "cumulative_score": 3934350},
    222: {"name": "Brigadier General Diamond (Tier 3)", "cumulative_score": 4034350},
    223: {"name": "General Diamond (Tier 1)", "cumulative_score": 4106850},
    224: {"name": "General Diamond (Tier 2)", "cumulative_score": 4191850},
    225: {"name": "General Diamond (Tier 3)", "cumulative_score": 4291850},
    226: {"name": "Cadet Onyx (Tier 1)", "cumulative_score": 4336850},
    227: {"name": "Cadet Onyx (Tier 2)", "cumulative_score": 4391850},
    228: {"name": "Cadet Onyx (Tier 3)", "cumulative_score": 4461850},
    229: {"name": "Private Onyx (Tier 1)", "cumulative_score": 4511850},
    230: {"name": "Private Onyx (Tier 2)", "cumulative_score": 4569350},
    231: {"name": "Private Onyx (Tier 3)", "cumulative_score": 4646850},
    232: {"name": "Lance Corporal Onyx (Tier 1)", "cumulative_score": 4699350},
    233: {"name": "Lance Corporal Onyx (Tier 2)", "cumulative_score": 4764350},
    234: {"name": "Lance Corporal Onyx (Tier 3)", "cumulative_score": 4846850},
    235: {"name": "Corporal Onyx (Tier 1)", "cumulative_score": 4904350},
    236: {"name": "Corporal Onyx (Tier 2)", "cumulative_score": 4974350},
    237: {"name": "Corporal Onyx (Tier 3)", "cumulative_score": 5064350},
    238: {"name": "Sergeant Onyx (Tier 1)", "cumulative_score": 5126850},
    239: {"name": "Sergeant Onyx (Tier 2)", "cumulative_score": 5204350},
    240: {"name": "Sergeant Onyx (Tier 3)", "cumulative_score": 5304350},
    241: {"name": "Staff Sergeant Onyx (Tier 1)", "cumulative_score": 5374350},
    242: {"name": "Staff Sergeant Onyx (Tier 2)", "cumulative_score": 5456850},
    243: {"name": "Staff Sergeant Onyx (Tier 3)", "cumulative_score": 5556850},
    244: {"name": "Gunnery Sergeant Onyx (Tier 1)", "cumulative_score": 5631850},
    245: {"name": "Gunnery Sergeant Onyx (Tier 2)", "cumulative_score": 5721850},
    246: {"name": "Gunnery Sergeant Onyx (Tier 3)", "cumulative_score": 5846850},
    247: {"name": "Master Sergeant Onyx (Tier 1)", "cumulative_score": 5929350},
    248: {"name": "Master Sergeant Onyx (Tier 2)", "cumulative_score": 6029350},
    249: {"name": "Master Sergeant Onyx (Tier 3)", "cumulative_score": 6154350},
    250: {"name": "Lieutenant Onyx (Tier 1)", "cumulative_score": 6244350},
    251: {"name": "Lieutenant Onyx (Tier 2)", "cumulative_score": 6344350},
    252: {"name": "Lieutenant Onyx (Tier 3)", "cumulative_score": 6494350},
    253: {"name": "Captain Onyx (Tier 1)", "cumulative_score": 6594350},
    254: {"name": "Captain Onyx (Tier 2)", "cumulative_score": 6719350},
    255: {"name": "Captain Onyx (Tier 3)", "cumulative_score": 6869350},
    256: {"name": "Major Onyx (Tier 1)", "cumulative_score": 6969350},
    257: {"name": "Major Onyx (Tier 2)", "cumulative_score": 7094350},
    258: {"name": "Major Onyx (Tier 3)", "cumulative_score": 7269350},
    259: {"name": "Lt Colonel Onyx (Tier 1)", "cumulative_score": 7394350},
    260: {"name": "Lt Colonel Onyx (Tier 2)", "cumulative_score": 7544350},
    261: {"name": "Lt Colonel Onyx (Tier 3)", "cumulative_score": 7719350},
    262: {"name": "Colonel Onyx (Tier 1)", "cumulative_score": 7844350},
    263: {"name": "Colonel Onyx (Tier 2)", "cumulative_score": 7994350},
    264: {"name": "Colonel Onyx (Tier 3)", "cumulative_score": 8194350},
    265: {"name": "Brigadier General Onyx (Tier 1)", "cumulative_score": 8344350},
    266: {"name": "Brigadier General Onyx (Tier 2)", "cumulative_score": 8519350},
    267: {"name": "Brigadier General Onyx (Tier 3)", "cumulative_score": 8744350},
    268: {"name": "General Onyx (Tier 1)", "cumulative_score": 8894350},
    269: {"name": "General Onyx (Tier 2)", "cumulative_score": 9069350},
    270: {"name": "General Onyx (Tier 3)", "cumulative_score": 9319350},
    # NOTE: Oddly the API does not seem to have a rank 271. Hero comes back as 272.
    # Therefore I duplicated Hero across 271 and 272 so that relative math still works.
    271: {"name": "Hero", "cumulative_score": 9319350},
    272: {"name": "Hero", "cumulative_score": 9319350},
}

GAME_VARIANT_CATEGORY_ATTRITION = 7
GAME_VARIANT_CATEGORY_CAPTURE_THE_FLAG = 15
GAME_VARIANT_CATEGORY_ELIMINATION = 8
GAME_VARIANT_CATEGORY_FIESTA = 9
GAME_VARIANT_CATEGORY_INFECTION = 22
GAME_VARIANT_CATEGORY_KING_OF_THE_HILL = 12
GAME_VARIANT_CATEGORY_LAND_GRAB = 39
GAME_VARIANT_CATEGORY_ODDBALL = 18
GAME_VARIANT_CATEGORY_SLAYER = 6
GAME_VARIANT_CATEGORY_STOCKPILE = 19
GAME_VARIANT_CATEGORY_STRONGHOLDS = 11
GAME_VARIANT_CATEGORY_TEAM_ESCALATION = 24
GAME_VARIANT_CATEGORY_TOTAL_CONTROL = 14

MAP_ID_AQUARIUS = "33c0766c-ef15-48f8-b298-34aba5bff3b4"
MAP_ID_ARGYLE = "dd600260-d91c-4d77-9990-3f35873c90a1"
MAP_ID_BAZAAR = "298d5036-cd43-47b3-a4bd-31e127566593"
MAP_ID_BEHEMOTH = "53136ad9-0fd6-4271-8752-31d114b9561e"
MAP_ID_BREAKER = "e6cbfe01-665b-4a8c-bf3a-d63a65a7c890"
MAP_ID_CATALYST = "e859cf75-9b8a-429a-91be-2376681c8537"
MAP_ID_CHASM = "fc1ced39-128b-439d-9b44-4710225090f3"
MAP_ID_CLIFFHANGER = "81274d6f-6a94-425a-a16e-3bdb1e2eea9d"
MAP_ID_DEADLOCK = "08607bf4-6abe-4a5b-9547-290a6cc1433e"
MAP_ID_DETACHMENT = "d39600e2-3c35-4a3a-bdf5-7b3cbdde98e1"
MAP_ID_DREDGE = "e4bb06db-065f-4902-b93b-d8dac315eac4"
MAP_ID_EMPYREAN = "d035fc3e-f298-4c14-9487-465be2e1dc1f"
MAP_ID_FORBIDDEN = "7e8b3a2c-459d-4f33-9066-66041b5a36c4"
MAP_ID_FOREST = "619bea21-f1e6-461f-8a7d-2bb4f905d0ca"
MAP_ID_FRAGMENTATION = "4f196016-0101-4844-8358-2504f7c44656"
MAP_ID_HIGHPOWER = "c494ef7c-d203-42a9-9c0f-b3f576334501"
MAP_ID_LAUNCH_SITE = "56a11b8c-64d1-4537-8893-a9241e4d5b93"
MAP_ID_LIVE_FIRE = "b6aca0c7-8ba7-4066-bf91-693571374c3c"
MAP_ID_OASIS = "6aa0a116-66a6-4242-a1b3-41aa417d6dc6"
MAP_ID_PRISM = "92d23264-d3b9-462e-adbc-8ddb44e81966"
MAP_ID_RECHARGE = "8420410b-044d-44d7-80b6-98a766c8c39f"
MAP_ID_SCARR = "247637f8-1ed2-47de-8ff0-fd4b68f50888"
MAP_ID_SOLITUDE = "f1cc3b4e-471c-4ec5-b855-1db7d9e6ce42"
MAP_ID_STREETS = "f0a1760f-0d4a-4bcc-ac7a-e8f9aee331dc"

MEDAL_ID_EXTERMINATION = 4100966367
MEDAL_ID_PERFECTION = 865763896

PLAYLIST_ID_BOT_BOOTCAMP = "a446725e-b281-414c-a21e-31b8700e95a1"
PLAYLIST_ID_RANKED_ARENA = "edfef3ac-9cbe-4fa2-b949-8f29deafd483"

SEARCH_ASSET_KIND_MAP = 2
SEARCH_ASSET_KIND_MODE = 6
SEARCH_ASSET_KIND_PREFAB = 4

SEASON_1_API_ID = "Seasons/Season6.json"
SEASON_1_RESET_API_ID = "Seasons/Season6-2.json"
SEASON_2_API_ID = "Seasons/Season7.json"
SEASON_WU_API_ID = "Seasons/Season-Winter-Break-22.json"
SEASON_3_API_ID = "Seasons/Season3.json"
SEASON_3_FIRST_DAY = datetime.date(year=2023, month=3, day=7)
SEASON_3_LAST_DAY = datetime.date(year=2023, month=6, day=19)
SEASON_3_START_TIME = datetime.datetime.fromisoformat("2023-03-07T18:00:00Z")
SEASON_3_END_TIME = datetime.datetime.fromisoformat("2023-06-20T17:00:00Z")
SEASON_3_RANKED_ARENA_PLAYLIST_ID = "edfef3ac-9cbe-4fa2-b949-8f29deafd483"
SEASON_3_DEV_MAP_IDS = {
    MAP_ID_AQUARIUS,
    MAP_ID_ARGYLE,
    MAP_ID_BAZAAR,
    MAP_ID_BEHEMOTH,
    MAP_ID_BREAKER,
    MAP_ID_CATALYST,
    MAP_ID_CHASM,
    MAP_ID_CLIFFHANGER,
    MAP_ID_DEADLOCK,
    MAP_ID_DETACHMENT,
    MAP_ID_EMPYREAN,
    MAP_ID_FRAGMENTATION,
    MAP_ID_HIGHPOWER,
    MAP_ID_LAUNCH_SITE,
    MAP_ID_LIVE_FIRE,
    MAP_ID_OASIS,
    MAP_ID_RECHARGE,
    MAP_ID_STREETS,
}
SEASON_4_API_ID = "Seasons/Season4.json"
SEASON_4_FIRST_DAY = datetime.date(year=2023, month=6, day=20)
SEASON_4_LAST_DAY = datetime.date(year=2023, month=10, day=17)
SEASON_4_START_TIME = datetime.datetime.fromisoformat("2023-06-20T17:00:00Z")
SEASON_4_END_TIME = datetime.datetime.fromisoformat("2023-10-17T17:00:00Z")
SEASON_4_RANKED_ARENA_PLAYLIST_ID = "edfef3ac-9cbe-4fa2-b949-8f29deafd483"
SEASON_4_DEV_MAP_IDS = {
    MAP_ID_AQUARIUS,
    MAP_ID_ARGYLE,
    MAP_ID_BAZAAR,
    MAP_ID_BEHEMOTH,
    MAP_ID_BREAKER,
    MAP_ID_CATALYST,
    MAP_ID_CHASM,
    MAP_ID_CLIFFHANGER,
    MAP_ID_DEADLOCK,
    MAP_ID_DETACHMENT,
    MAP_ID_DREDGE,
    MAP_ID_EMPYREAN,
    MAP_ID_FOREST,
    MAP_ID_FRAGMENTATION,
    MAP_ID_HIGHPOWER,
    MAP_ID_LAUNCH_SITE,
    MAP_ID_LIVE_FIRE,
    MAP_ID_OASIS,
    MAP_ID_RECHARGE,
    MAP_ID_SCARR,
    MAP_ID_SOLITUDE,
    MAP_ID_STREETS,
}
SEASON_5_PART_1_API_ID = "Csr/Seasons/CsrSeason5-1.json"
SEASON_5_PART_2_API_ID = "Csr/Seasons/CsrSeason5-2.json"
SEASON_5_PART_3_API_ID = "Csr/Seasons/CsrSeason5-3.json"
SEASON_5_FIRST_DAY = datetime.date(year=2023, month=10, day=17)
SEASON_5_LAST_DAY = datetime.date(year=2024, month=1, day=31)
SEASON_5_PART_1_START_TIME = datetime.datetime.fromisoformat("2023-10-17T17:00:00Z")
SEASON_5_PART_1_END_TIME = datetime.datetime.fromisoformat("2023-11-14T17:00:00Z")
SEASON_5_PART_2_START_TIME = SEASON_5_PART_1_END_TIME
SEASON_5_PART_2_END_TIME = datetime.datetime.fromisoformat("2023-12-19T17:00:00Z")
SEASON_5_PART_3_START_TIME = SEASON_5_PART_2_END_TIME
SEASON_5_PART_3_END_TIME = datetime.datetime.fromisoformat("2024-01-30T17:00:00Z")
SEASON_5_START_TIME = SEASON_5_PART_1_START_TIME
SEASON_5_END_TIME = SEASON_5_PART_3_END_TIME
SEASON_5_RANKED_ARENA_PLAYLIST_ID = "edfef3ac-9cbe-4fa2-b949-8f29deafd483"
SEASON_5_DEV_MAP_IDS = {
    MAP_ID_AQUARIUS,
    MAP_ID_ARGYLE,
    MAP_ID_BAZAAR,
    MAP_ID_BEHEMOTH,
    MAP_ID_BREAKER,
    MAP_ID_CATALYST,
    MAP_ID_CHASM,
    MAP_ID_CLIFFHANGER,
    MAP_ID_DEADLOCK,
    MAP_ID_DETACHMENT,
    MAP_ID_DREDGE,
    MAP_ID_EMPYREAN,
    MAP_ID_FORBIDDEN,
    MAP_ID_FOREST,
    MAP_ID_FRAGMENTATION,
    MAP_ID_HIGHPOWER,
    MAP_ID_LAUNCH_SITE,
    MAP_ID_LIVE_FIRE,
    MAP_ID_OASIS,
    MAP_ID_PRISM,
    MAP_ID_RECHARGE,
    MAP_ID_SCARR,
    MAP_ID_SOLITUDE,
    MAP_ID_STREETS,
}
SEASON_DATA_DICT = {
    "3": {
        "api_id": SEASON_3_API_ID,
        "first_day": SEASON_3_FIRST_DAY,
        "last_day": SEASON_3_LAST_DAY,
        "start_time": SEASON_3_START_TIME,
        "end_time": SEASON_3_END_TIME,
        "ranked_arena_playlist_id": SEASON_3_RANKED_ARENA_PLAYLIST_ID,
        "dev_map_ids": SEASON_3_DEV_MAP_IDS,
    },
    "4": {
        "api_id": SEASON_4_API_ID,
        "first_day": SEASON_4_FIRST_DAY,
        "last_day": SEASON_4_LAST_DAY,
        "start_time": SEASON_4_START_TIME,
        "end_time": SEASON_4_END_TIME,
        "ranked_arena_playlist_id": SEASON_4_RANKED_ARENA_PLAYLIST_ID,
        "dev_map_ids": SEASON_4_DEV_MAP_IDS,
    },
    "5": {
        "api_ids": [
            SEASON_5_PART_1_API_ID,
            SEASON_5_PART_2_API_ID,
            SEASON_5_PART_3_API_ID,
        ],
        "first_day": SEASON_5_FIRST_DAY,
        "last_day": SEASON_5_LAST_DAY,
        "start_time": SEASON_5_START_TIME,
        "end_time": SEASON_5_END_TIME,
        "ranked_arena_playlist_id": SEASON_5_RANKED_ARENA_PLAYLIST_ID,
        "dev_map_ids": SEASON_5_DEV_MAP_IDS,
    },
}
