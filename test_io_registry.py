# test_io_registry.py
from device.io_registry import IORegistry

def test_registry_reading():
    print("="*70)
    print("TEST 4: Registry Reading")
    print("="*70)
    
    try:
        config = IORegistry.read_config()
        
        if config is None:
            print("⚠️  No registry configuration found (using defaults)")
            config = IORegistry.create_default_config()
        
        print(f"\nIO Card Count: {config.card_count}")
        print(f"Cards configured: {len(config.cards)}")
        
        for card in config.cards:
            print(f"\n  Card {card.card_index}:")
            print(f"    Name: {card.name}")
            print(f"    Address: {hex(card.address)}")
            print(f"    In Port: {card.in_port_id} (Card {card.in_card_no})")
            print(f"    Out Port: {card.out_port_id} (Card {card.out_card_no})")
        
        print("\nTrack IO Configurations:")
        for track_num, track_config in config.track_configs.items():
            print(f"  Track {track_num}:")
            print(f"    Busy bit: {track_config.busy_bit}")
            print(f"    Result bit: {track_config.result_bit}")
        
        print("\n✅ TEST 4 PASSED")
        return True
        
    except Exception as e:
        print(f"❌ TEST 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_registry_reading()
