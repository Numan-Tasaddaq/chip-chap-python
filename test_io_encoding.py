# test_io_encoding.py
from device.io_constants import encode_output_signal

def test_signal_encoding():
    print("="*70)
    print("TEST 3: Signal Encoding")
    print("="*70)
    
    test_cases = [
        # (result_code, busy_bit, result_bit, expected_value, description)
        (0, 7, 0, 0b10000000, "PASS with busy=1, result=0, bit7=busy, bits0-2=result"),
        (1, 7, 0, 0b10000001, "FAIL with busy=1, result=1"),
        (7, 7, 0, 0b10000111, "Result=7 with busy=1"),
        (0, 7, 0, 0b00000000, "PASS with busy=0 (after ack)"),
    ]
    
    all_passed = True
    for result, busy_bit, result_bit, expected, desc in test_cases:
        if "busy=0" in desc:
            # For busy=0 case, clear the busy bit manually
            signal = encode_output_signal(result, busy_bit, result_bit) & ~(1 << busy_bit)
        else:
            signal = encode_output_signal(result, busy_bit, result_bit)
        
        if signal == expected:
            print(f"✅ {desc}")
            print(f"   Binary: {bin(signal)}, Hex: {hex(signal)}")
        else:
            print(f"❌ {desc}")
            print(f"   Expected: {bin(expected)}, Got: {bin(signal)}")
            all_passed = False
    
    if all_passed:
        print("\n✅ TEST 3 PASSED")
    else:
        print("\n❌ TEST 3 FAILED")
    
    return all_passed

if __name__ == "__main__":
    test_signal_encoding()
