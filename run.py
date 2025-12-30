# run.py - ENTRY POINT
import os
import sys
import logging

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('pricetracker.log')
    ]
)

logger = logging.getLogger(__name__)

try:
    from backend.app import create_app
    
    app = create_app()
    
    if __name__ == '__main__':
        print("\n" + "="*60)
        print("🚀 PRICETRACKER - E-COMMERCE PRICE COMPARISON")
        print("="*60)
        print("\n🌐 ACCESS LINKS:")
        print("  📊 Dashboard:    http://localhost:5000")
        print("  🔍 Search:       http://localhost:5000/product_search.html")
        print("  💖 Wishlist:     http://localhost:5000/wishlist.html")
        print("  👤 Profile:      http://localhost:5000/profile.html")
        print("  🔐 Auth:         http://localhost:5000/auth.html")
        print("\n⚡ API ENDPOINTS:")
        print("  📡 Health Check: http://localhost:5000/api/health")
        print("  🔍 Search API:   http://localhost:5000/api/search")
        print("\n⚙️  FEATURES:")
        print("  ✅ Real-time scraping: Amazon & Flipkart")
        print("  📈 Demo data: Myntra & Meesho")
        print("  📊 Price tracking & alerts")
        print("  💾 Database: SQLite (pricetracker.db)")
        print("  📝 Logs: pricetracker.log")
        print("\n" + "="*60)
        print("🛑 Press Ctrl+C to stop the server")
        print("="*60 + "\n")
        
        # Start the server
        app.run(debug=True, host='0.0.0.0', port=5000)
        
except Exception as e:
    logger.error(f"Failed to start application: {e}")
    print(f"❌ Error: {e}")
    print("Please check your installation and file structure.")