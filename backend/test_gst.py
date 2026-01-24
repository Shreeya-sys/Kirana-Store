from gst_engine import calculate_gst

def test_gst():
    # Test Sugar (5%)
    res = calculate_gst("1701", 100)
    print(f"Sugar (100): Tax={res['total_tax']}, Total={res['total_amount']}")
    assert res['total_tax'] == 5.0
    assert res['total_amount'] == 105.0

    # Test Cosmetics (18%)
    res = calculate_gst("3304", 1000)
    print(f"Cosmetics (1000): Tax={res['total_tax']}, Total={res['total_amount']}")
    assert res['total_tax'] == 180.0
    assert res['total_amount'] == 1180.0

    # Test Unknown (18% default)
    res = calculate_gst("9999", 100)
    print(f"Unknown (100): Tax={res['total_tax']}, Total={res['total_amount']}")
    assert res['total_tax'] == 18.0

if __name__ == "__main__":
    test_gst()
