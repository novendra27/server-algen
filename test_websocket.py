"""
Test WebSocket Client - Python
Debug WebSocket connection untuk GA KKM Optimization
"""

import asyncio
import websockets
import json

async def test_websocket(job_id: str):
    """Test WebSocket connection dengan job_id"""
    
    uri = f"ws://localhost:8000/ws/{job_id}"
    
    print("=" * 80)
    print("🔌 WebSocket Debugger - GA KKM Optimization")
    print("=" * 80)
    print(f"📡 Connecting to: {uri}")
    print()
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected successfully!")
            print("⏳ Waiting for messages...\n")
            
            message_count = 0
            
            # Receive messages
            async for message in websocket:
                message_count += 1
                data = json.loads(message)
                
                print(f"📨 Message #{message_count}")
                print(f"   Status: {data.get('status', 'unknown')}")
                print(f"   Message: {data.get('message', 'No message')}")
                
                # Check if completed
                if data.get('status') == 'completed':
                    print("\n🎉 Optimization completed!")
                    
                    result = data.get('result', {})
                    stats = result.get('statistics', {})
                    
                    print("\n📊 Statistics:")
                    print(f"   Best Fitness: {stats.get('best_fitness', 'N/A')}/{stats.get('max_fitness', 'N/A')}")
                    print(f"   Normalized: {stats.get('best_normalized_fitness', 'N/A'):.2%}")
                    print(f"   Generations: {stats.get('total_generations', 'N/A')}")
                    print(f"   Execution Time: {stats.get('execution_time_seconds', 'N/A')} seconds")
                    
                    kelompok_list = result.get('kelompok_list', [])
                    print(f"\n👥 Total Kelompok: {len(kelompok_list)}")
                    
                    # Show first 3 groups as sample
                    print("\n📋 Sample Groups (first 3):")
                    for i, kelompok in enumerate(kelompok_list[:3], 1):
                        print(f"   Kelompok {i}: {len(kelompok)} members - {kelompok[:5]}{'...' if len(kelompok) > 5 else ''}")
                    
                    # Full result JSON
                    print("\n" + "=" * 80)
                    print("📄 Full Result JSON:")
                    print("=" * 80)
                    print(json.dumps(result, indent=2))
                    
                elif data.get('status') == 'failed' or data.get('status') == 'error':
                    print("\n❌ Optimization failed!")
                    print(f"   Error: {data.get('error', 'Unknown error')}")
                
                elif data.get('status') == 'processing':
                    print("   ⏳ Still processing...")
                
                print()
            
            print("🔌 WebSocket connection closed by server")
            
    except websockets.exceptions.ConnectionClosed as e:
        print(f"\n⚠️  Connection closed: Code {e.code}, Reason: {e.reason}")
    except websockets.exceptions.WebSocketException as e:
        print(f"\n❌ WebSocket error: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    
    print("\n" + "=" * 80)
    print("✅ Test completed")
    print("=" * 80)


async def main():
    """Main function"""
    
    # Ganti dengan job_id yang Anda dapatkan dari POST /api/optimize
    job_id = "550e8400-e29b-41d4-a716-446655440000"
    
    print("\n💡 Tips:")
    print("   1. Kirim request ke POST /api/optimize terlebih dahulu")
    print("   2. Copy job_id dari response")
    print("   3. Ganti nilai job_id di bawah ini\n")
    
    await test_websocket(job_id)


if __name__ == "__main__":
    # Run async main
    asyncio.run(main())
