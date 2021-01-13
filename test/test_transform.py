from vicarutil.transforms import *

# BSQ
bsq: np.ndarray = np.asarray([
    [
        [
            'B0L0S0', 'B0L0S1', 'B0L0S2'
        ],
        [
            'B0L1S0', 'B0L1S1', 'B0L1S2'
        ],
        [
            'B0L2S0', 'B0L2S1', 'B0L2S2'
        ],
    ],
    [
        [
            'B1L0S0', 'B1L0S1', 'B1L0S2'
        ],
        [
            'B1L1S0', 'B1L1S1', 'B1L1S2'
        ],
        [
            'B1L2S0', 'B1L2S1', 'B1L2S2'
        ],
    ]
])

# BIP
bip: np.ndarray = np.asarray([
    [
        [
            'B0L0S0', 'B1L0S0'
        ],
        [
            'B0L0S1', 'B1L0S1'
        ],
        [
            'B0L0S2', 'B1L0S2'
        ]
    ],
    [
        [
            'B0L1S0', 'B1L1S0'
        ],
        [
            'B0L1S1', 'B1L1S1'
        ],
        [
            'B0L1S2', 'B1L1S2'
        ]
    ],
    [
        [
            'B0L2S0', 'B1L2S0'
        ],
        [
            'B0L2S1', 'B1L2S1'
        ],
        [
            'B0L2S2', 'B1L2S2'
        ]
    ]
])

# BIL
bil: np.ndarray = np.asarray([
    [
        [
            'B0L0S0', 'B0L0S1', 'B0L0S2'
        ],
        [
            'B1L0S0', 'B1L0S1', 'B1L0S2'
        ]
    ],
    [
        [
            'B0L1S0', 'B0L1S1', 'B0L1S2'
        ],
        [
            'B1L1S0', 'B1L1S1', 'B1L1S2'
        ]
    ],
    [
        [
            'B0L2S0', 'B0L2S1', 'B0L2S2'
        ],
        [
            'B1L2S0', 'B1L2S1', 'B1L2S2'
        ]
    ]
])


def transform(label: str, reference: np.ndarray, transformed: np.ndarray):
    print("  - " + label)
    print("    - ref: " + str(reference.shape))
    print("    - got: " + str(transformed.shape))
    try:
        assert (reference == transformed).all()
        print("    - values correct")
    except AssertionError as e:
        print("Failed: ")
        print("  expected:")
        print(reference)
        print("  found:")
        print(transformed)
        raise e


def test_transform():
    print("\nTesting BSQ transform:")
    transform("BSQ to BIP", bip, bsq_to_bip(bsq))
    transform("BIP to BSQ", bsq, bip_to_bsq(bip))
    transform("BSQ to BIL", bil, bsq_to_bil(bsq))
    transform("BIL to BSQ", bsq, bil_to_bsq(bil))
    transform("BIL to BIP", bip, bil_to_bip(bil))
    transform("BIP to BIL", bil, bip_to_bil(bip))
    transform("BSQ to BIL to BIP", bip, bil_to_bip(bsq_to_bil(bsq)))
    transform("BIP to BIL to BSQ", bsq, bil_to_bsq(bip_to_bil(bip)))
    transform("Cycle", bsq, bil_to_bsq(bip_to_bil(bsq_to_bip(bsq))))
