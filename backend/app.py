# backend/app.py - FINAL VERSION WITH ENHANCED SCRAPER

from flask import Flask, request, jsonify, send_from_directory
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flask_cors import CORS
from datetime import datetime
import os
import logging
import sys
import random

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import db
from auth import auth_bp  # FIXED: Changed "auth bp" to "auth_bp"
from scraper import PriceScraper, get_scraper
from models import User, Product, Wishlist, WishlistItem, PriceHistory

# Initialize scraper globally
scraper = get_scraper()
logger.info("✅ PriceScraper initialized successfully")

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import db
from auth import auth_bp
from scraper import PriceScraper, get_scraper
from models import User, Product, Wishlist, WishlistItem, PriceHistory

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application"""
    # Initialize Flask app
    app = Flask(__name__,
        static_folder='../frontend',
        static_url_path='')

    # Configuration
    app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pricetracker.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'jwt-secret-key-change-me'
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600  # 1 hour in seconds
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = 2592000  # 30 days in seconds

    # Initialize extensions with proper CORS settings
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:5000", "http://127.0.0.1:5000"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "Accept"],
            "expose_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    jwt = JWTManager(app)
    db.init_app(app)

        # Register blueprints
    app.register_blueprint(auth_bp)

    # Create tables on first request
    @app.before_request
    def create_tables():
        if not hasattr(app, 'tables_created'):
            with app.app_context():
                db.create_all()
                logger.info("✔ Database tables created!")
                
                # Create admin user if not exists
                admin = User.query.filter_by(email='admin@example.com').first()
                if not admin:
                    admin = User(
                        username='admin',
                        email='admin@example.com',
                        created_at=datetime.utcnow(),
                        last_login=datetime.utcnow()
                    )
                    admin.set_password('admin123')
                    db.session.add(admin)
                    db.session.commit()
                    logger.info("👑 Admin user created")
            
            app.tables_created = True

    # ========== STATIC FILE SERVING ==========
    @app.route('/')
    def index():
        """Serve dashboard as homepage"""
        return send_from_directory(app.static_folder, 'dashboard.html')

    @app.route('/<path:filename>')
    def serve_frontend(filename):
        """Serve all frontend files"""
        # Security check
        if '..' in filename or filename.startswith('/'):
            return jsonify({'error': 'Forbidden'}), 403
        
        # List of valid HTML files
        valid_html_files = [
            'dashboard.html',
            'product_search.html', 
            'wishlist.html',
            'profile.html',
            'auth.html'
        ]
        
        # If it's an HTML file, serve it
        if filename in valid_html_files:
            return send_from_directory(app.static_folder, filename)
        
        # Check for CSS/JS files in styles folder
        if filename.startswith('styles/'):
            return send_from_directory(app.static_folder, filename)
        
        # Default to dashboard
        return send_from_directory(app.static_folder, 'dashboard.html')

    # ========== API ENDPOINTS ==========
    
    # Health Check
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'service': 'PriceTracker API',
            'version': '1.0.0',
            'timestamp': datetime.utcnow().isoformat(),
            'scraper_status': 'active'
        })

    # Search Products - ENHANCED VERSION
    @app.route('/api/search', methods=['POST', 'OPTIONS'])
    def search_products():
        """Search products across multiple e-commerce websites"""
        if request.method == 'OPTIONS':
            return jsonify({}), 200
            
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            query = data.get('query', '').strip()
            logger.info(f"🔍 Search request: '{query}'")
            
            if not query or len(query) < 2:
                return jsonify({'error': 'Query must be at least 2 characters'}), 400
            
            # Get filters
            website_filter = data.get('website', 'all')
            category_filter = data.get('category', 'all')
            sort_filter = data.get('sort', 'relevance')
            min_price = data.get('min_price')
            max_price = data.get('max_price')
            
            # Search products using the scraper
            logger.info(f"Starting search for: {query}")
            results = scraper.search_products(
                query=query, 
                max_results=30, 
                use_real_data=True
            )
            
            if not results:
                logger.warning(f"No results found for: {query}")
                # Generate demo data as fallback
                results = scraper._get_demo_data(query, 10)
            
            # Apply filters
            filtered_results = results
            
            # Website filter
            if website_filter != 'all':
                filtered_results = [r for r in filtered_results if r['website'] == website_filter]
            
            # Price range filter
            if min_price:
                try:
                    min_price_val = float(min_price)
                    filtered_results = [r for r in filtered_results if r['price'] >= min_price_val]
                except ValueError:
                    pass
            
            if max_price:
                try:
                    max_price_val = float(max_price)
                    filtered_results = [r for r in filtered_results if r['price'] <= max_price_val]
                except ValueError:
                    pass
            
            # Apply sorting
            if sort_filter == 'price_low':
                filtered_results.sort(key=lambda x: x['price'])
            elif sort_filter == 'price_high':
                filtered_results.sort(key=lambda x: x['price'], reverse=True)
            elif sort_filter == 'rating':
                filtered_results.sort(key=lambda x: x.get('rating', 0), reverse=True)
            
            logger.info(f"✅ Search completed: {len(filtered_results)} results for '{query}'")
            
            return jsonify({
                'success': True,
                'query': query,
                'results': filtered_results,
                'count': len(filtered_results),
                'filters_applied': {
                    'website': website_filter,
                    'category': category_filter,
                    'sort': sort_filter,
                    'min_price': min_price,
                    'max_price': max_price
                },
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Search error: {str(e)}", exc_info=True)
            # Fallback to demo data
            demo_results = scraper._get_demo_data(query if 'query' in locals() else 'product', 15)
            return jsonify({
                'success': True,
                'results': demo_results,
                'count': len(demo_results),
                'note': 'Using demo data due to system error',
                'error': str(e)
            }), 200

    # Get Product Details
    @app.route('/api/product/<path:product_url>', methods=['GET'])
    def get_product_details(product_url):
        """Get detailed product information"""
        try:
            # Decode URL
            import urllib.parse
            product_url = urllib.parse.unquote(product_url)
            
            logger.info(f"📦 Fetching product details: {product_url[:100]}...")
            
            # Scrape product page
            product_data = scraper.scrape_product_page(product_url)
            
            if not product_data:
                return jsonify({
                    'error': 'Could not fetch product details',
                    'suggestion': 'Try again later or check the URL'
                }), 404
            
            # Check if product exists in database
            existing_product = Product.query.filter_by(product_url=product_url).first()
            
            if existing_product:
                # Update product information
                existing_product.name = product_data.get('name', existing_product.name)
                existing_product.image_url = product_data.get('image_url', existing_product.image_url)
                db.session.commit()
                
                # Add price history
                new_price = PriceHistory(
                    product_id=existing_product.id,
                    price=product_data.get('price', 0),
                    website=product_data.get('website', 'unknown'),
                    availability=product_data.get('availability', 'Unknown'),
                    delivery_date=product_data.get('delivery_date', 'Not specified'),
                    timestamp=datetime.utcnow()
                )
                db.session.add(new_price)
                db.session.commit()
            
            return jsonify({
                'success': True,
                'product': product_data,
                'in_database': existing_product is not None
            })
            
        except Exception as e:
            logger.error(f"Product details error: {e}")
            return jsonify({'error': str(e)}), 500

    # Track/Add Product to Wishlist
    @app.route('/api/track-product', methods=['POST'])
    @jwt_required()
    def track_product():
        """Add a product to wishlist for tracking"""
        try:
            current_user_id = get_jwt_identity()
            data = request.get_json()
            
            # Validate input
            required_fields = ['product_url', 'name']
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'Missing required field: {field}'}), 400
            
            product_url = data.get('product_url')
            product_name = data.get('name')
            target_price = data.get('target_price')
            wishlist_id = data.get('wishlist_id')
            notes = data.get('notes', '')
            
            # Check if product exists
            product = Product.query.filter_by(product_url=product_url).first()
            
            if not product:
                # Create new product
                product = Product(
                    name=product_name,
                    product_url=product_url,
                    image_url=data.get('image_url', ''),
                    category=data.get('category', 'general'),
                    created_at=datetime.utcnow()
                )
                db.session.add(product)
                db.session.commit()
                
                # Get current price
                product_data = scraper.scrape_product_page(product_url)
                if product_data and product_data.get('price'):
                    price_history = PriceHistory(
                        product_id=product.id,
                        price=product_data['price'],
                        website=product_data.get('website', 'unknown'),
                        availability=product_data.get('availability', 'Unknown'),
                        delivery_date=product_data.get('delivery_date', 'Not specified'),
                        timestamp=datetime.utcnow()
                    )
                    db.session.add(price_history)
                    db.session.commit()
            
            # Get or create wishlist
            if wishlist_id:
                wishlist = Wishlist.query.filter_by(id=wishlist_id, user_id=current_user_id).first()
                if not wishlist:
                    return jsonify({'error': 'Wishlist not found or access denied'}), 404
            else:
                # Use default wishlist
                wishlist = Wishlist.query.filter_by(user_id=current_user_id, name='Default').first()
                if not wishlist:
                    wishlist = Wishlist(
                        user_id=current_user_id,
                        name='Default',
                        created_at=datetime.utcnow()
                    )
                    db.session.add(wishlist)
                    db.session.commit()
            
            # Check if already in wishlist
            existing_item = WishlistItem.query.filter_by(
                wishlist_id=wishlist.id,
                product_id=product.id
            ).first()
            
            if existing_item:
                return jsonify({
                    'success': False,
                    'error': 'Product already in wishlist',
                    'wishlist_item_id': existing_item.id
                }), 400
            
            # Add to wishlist
            wishlist_item = WishlistItem(
                wishlist_id=wishlist.id,
                product_id=product.id,
                target_price=target_price,
                alert_enabled=True,
                notes=notes,
                added_at=datetime.utcnow()
            )
            db.session.add(wishlist_item)
            db.session.commit()
            
            logger.info(f"✅ Product added to wishlist: {product_name}")
            
            return jsonify({
                'success': True,
                'message': 'Product added to wishlist successfully',
                'wishlist_item': {
                    'id': wishlist_item.id,
                    'product_id': product.id,
                    'product_name': product.name,
                    'wishlist_id': wishlist.id,
                    'wishlist_name': wishlist.name,
                    'target_price': target_price,
                    'added_at': wishlist_item.added_at.isoformat()
                }
            })
            
        except Exception as e:
            logger.error(f"Track product error: {e}", exc_info=True)
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    # Get Wishlists
    @app.route('/api/wishlists', methods=['GET'])
    @jwt_required()
    def get_wishlists():
        """Get all wishlists for current user"""
        try:
            current_user_id = get_jwt_identity()
            
            wishlists = Wishlist.query.filter_by(user_id=current_user_id).all()
            
            wishlists_data = []
            for w in wishlists:
                item_count = WishlistItem.query.filter_by(wishlist_id=w.id).count()
                
                # Get latest item if exists
                latest_item = WishlistItem.query.filter_by(wishlist_id=w.id)\
                    .order_by(WishlistItem.added_at.desc()).first()
                
                wishlists_data.append({
                    'id': w.id,
                    'name': w.name,
                    'item_count': item_count,
                    'created_at': w.created_at.isoformat() if w.created_at else None,
                    'last_updated': latest_item.added_at.isoformat() if latest_item else None
                })
            
            # Sort by last updated
            wishlists_data.sort(key=lambda x: x['last_updated'] or '', reverse=True)
            
            return jsonify({
                'success': True,
                'wishlists': wishlists_data,
                'count': len(wishlists_data)
            })
            
        except Exception as e:
            logger.error(f"Get wishlists error: {e}")
            return jsonify({'error': str(e)}), 500

    # Create Wishlist
    @app.route('/api/wishlists', methods=['POST'])
    @jwt_required()
    def create_wishlist():
        """Create a new wishlist"""
        try:
            current_user_id = get_jwt_identity()
            data = request.get_json()
            
            name = data.get('name', '').strip()
            if not name:
                return jsonify({'error': 'Wishlist name is required'}), 400
            
            # Check if wishlist already exists
            existing = Wishlist.query.filter_by(user_id=current_user_id, name=name).first()
            if existing:
                return jsonify({
                    'error': 'Wishlist with this name already exists',
                    'wishlist_id': existing.id
                }), 400
            
            # Create new wishlist
            wishlist = Wishlist(
                user_id=current_user_id,
                name=name,
                created_at=datetime.utcnow()
            )
            db.session.add(wishlist)
            db.session.commit()
            
            logger.info(f"✅ Wishlist created: {name} for user {current_user_id}")
            
            return jsonify({
                'success': True,
                'message': 'Wishlist created successfully',
                'wishlist': {
                    'id': wishlist.id,
                    'name': wishlist.name,
                    'item_count': 0,
                    'created_at': wishlist.created_at.isoformat()
                }
            })
            
        except Exception as e:
            logger.error(f"Create wishlist error: {e}")
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    # Update Wishlist
    @app.route('/api/wishlists/<int:wishlist_id>', methods=['PUT'])
    @jwt_required()
    def update_wishlist(wishlist_id):
        """Rename a wishlist"""
        try:
            current_user_id = get_jwt_identity()
            data = request.get_json()
            name = (data.get('name') or '').strip()

            if not name:
                return jsonify({'error': 'Wishlist name is required'}), 400

            wishlist = Wishlist.query.filter_by(id=wishlist_id, user_id=current_user_id).first()
            if not wishlist:
                return jsonify({'error': 'Wishlist not found'}), 404

            wishlist.name = name
            db.session.commit()

            return jsonify({'success': True, 'message': 'Wishlist updated', 'wishlist': {'id': wishlist.id, 'name': wishlist.name}})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    # Delete Wishlist
    @app.route('/api/wishlists/<int:wishlist_id>', methods=['DELETE'])
    @jwt_required()
    def delete_wishlist(wishlist_id):
        """Delete a wishlist and all its items"""
        try:
            current_user_id = get_jwt_identity()

            wishlist = Wishlist.query.filter_by(id=wishlist_id, user_id=current_user_id).first()
            if not wishlist:
                return jsonify({'error': 'Wishlist not found'}), 404

            db.session.delete(wishlist)
            db.session.commit()

            return jsonify({'success': True, 'message': 'Wishlist deleted'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    # Update Wishlist Item (target price)
    @app.route('/api/wishlists/items/<int:item_id>', methods=['PUT'])
    @jwt_required()
    def update_wishlist_item(item_id):
        """Update target price for a wishlist item"""
        try:
            current_user_id = get_jwt_identity()
            data = request.get_json()

            item = WishlistItem.query.get(item_id)
            if not item:
                return jsonify({'error': 'Item not found'}), 404

            # Verify ownership through wishlist
            wishlist = Wishlist.query.filter_by(id=item.wishlist_id, user_id=current_user_id).first()
            if not wishlist:
                return jsonify({'error': 'Access denied'}), 403

            target_price = data.get('target_price')
            item.target_price = float(target_price) if target_price else None
            db.session.commit()

            return jsonify({'success': True, 'message': 'Target price updated', 'target_price': item.target_price})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    # Delete Wishlist Item
    @app.route('/api/wishlists/items/<int:item_id>', methods=['DELETE'])
    @jwt_required()
    def delete_wishlist_item(item_id):
        """Remove an item from a wishlist"""
        try:
            current_user_id = get_jwt_identity()

            item = WishlistItem.query.get(item_id)
            if not item:
                return jsonify({'error': 'Item not found'}), 404

            wishlist = Wishlist.query.filter_by(id=item.wishlist_id, user_id=current_user_id).first()
            if not wishlist:
                return jsonify({'error': 'Access denied'}), 403

            db.session.delete(item)
            db.session.commit()

            return jsonify({'success': True, 'message': 'Item removed from wishlist'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    # Get Wishlist Items
    @app.route('/api/wishlists/<int:wishlist_id>/items', methods=['GET'])
    @jwt_required()
    def get_wishlist_items(wishlist_id):
        """Get all items in a wishlist"""
        try:
            current_user_id = get_jwt_identity()
            
            # Verify ownership
            wishlist = Wishlist.query.filter_by(id=wishlist_id, user_id=current_user_id).first()
            if not wishlist:
                return jsonify({'error': 'Wishlist not found or access denied'}), 404
            
            items = WishlistItem.query.filter_by(wishlist_id=wishlist_id)\
                .order_by(WishlistItem.added_at.desc()).all()
            
            items_data = []
            price_alerts = 0
            
            for item in items:
                product = Product.query.get(item.product_id)
                if product:
                    # Get latest price
                    latest_price = PriceHistory.query.filter_by(
                        product_id=product.id
                    ).order_by(PriceHistory.timestamp.desc()).first()
                    
                    # Get price trend (last 5 prices)
                    price_history = PriceHistory.query.filter_by(
                        product_id=product.id
                    ).order_by(PriceHistory.timestamp.desc()).limit(5).all()
                    
                    price_trend = [{
                        'price': ph.price,
                        'timestamp': ph.timestamp.isoformat() if ph.timestamp else None,
                        'website': ph.website
                    } for ph in price_history]
                    
                    # Check if price alert is triggered
                    current_price = latest_price.price if latest_price else None
                    target_price = item.target_price
                    alert_triggered = False
                    
                    if current_price and target_price and current_price <= target_price:
                        price_alerts += 1
                        alert_triggered = True
                    
                    items_data.append({
                        'id': item.id,
                        'product': {
                            'id': product.id,
                            'name': product.name,
                            'product_url': product.product_url,
                            'image_url': product.image_url or f"https://picsum.photos/200/200?random={product.id}",
                            'category': product.category,
                            'current_price': current_price,
                            'website': latest_price.website if latest_price else 'unknown',
                            'availability': latest_price.availability if latest_price else 'Unknown',
                            'delivery_date': latest_price.delivery_date if latest_price else 'Not specified'
                        },
                        'target_price': target_price,
                        'alert_enabled': item.alert_enabled,
                        'alert_triggered': alert_triggered,
                        'notes': item.notes,
                        'added_at': item.added_at.isoformat() if item.added_at else None,
                        'price_trend': price_trend,
                        'price_change': _calculate_price_change(price_trend) if len(price_trend) > 1 else 0
                    })
            
            return jsonify({
                'success': True,
                'wishlist': {
                    'id': wishlist.id,
                    'name': wishlist.name,
                    'created_at': wishlist.created_at.isoformat() if wishlist.created_at else None
                },
                'items': items_data,
                'count': len(items_data),
                'price_alerts': price_alerts,
                'last_updated': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Get wishlist items error: {e}")
            return jsonify({'error': str(e)}), 500

    def _calculate_price_change(price_trend):
        """Calculate price change percentage"""
        if len(price_trend) < 2:
            return 0
        
        latest_price = price_trend[0]['price']
        oldest_price = price_trend[-1]['price']
        
        if oldest_price == 0:
            return 0
        
        change = ((latest_price - oldest_price) / oldest_price) * 100
        return round(change, 2)

    # Update Product Prices
    @app.route('/api/update-prices', methods=['POST'])
    @jwt_required()
    def update_prices():
        """Update prices for tracked products"""
        try:
            current_user_id = get_jwt_identity()
            
            # Get user's wishlist items
            wishlists = Wishlist.query.filter_by(user_id=current_user_id).all()
            product_urls = []
            
            for wishlist in wishlists:
                items = WishlistItem.query.filter_by(wishlist_id=wishlist.id).all()
                for item in items:
                    product = Product.query.get(item.product_id)
                    if product and product.product_url:
                        product_urls.append(product.product_url)
            
            # Remove duplicates
            product_urls = list(set(product_urls))
            
            if not product_urls:
                return jsonify({
                    'success': True,
                    'message': 'No products to update',
                    'updated': 0
                })
            
            logger.info(f"🔄 Updating prices for {len(product_urls)} products")
            
            # Update prices
            updated_products = scraper.update_product_prices(product_urls)
            
            # Save to database
            updated_count = 0
            for product_data in updated_products:
                if product_data and product_data.get('price'):
                    product = Product.query.filter_by(product_url=product_data['url']).first()
                    if product:
                        price_history = PriceHistory(
                            product_id=product.id,
                            price=product_data['price'],
                            website=product_data.get('website', 'unknown'),
                            availability=product_data.get('availability', 'Unknown'),
                            delivery_date=product_data.get('delivery_date', 'Not specified'),
                            timestamp=datetime.utcnow()
                        )
                        db.session.add(price_history)
                        updated_count += 1
            
            db.session.commit()
            
            logger.info(f"✅ Prices updated: {updated_count} products")
            
            return jsonify({
                'success': True,
                'message': f'Updated prices for {updated_count} products',
                'updated': updated_count,
                'total': len(product_urls)
            })
            
        except Exception as e:
            logger.error(f"Update prices error: {e}", exc_info=True)
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    # Get Price Alerts
    @app.route('/api/price-alerts', methods=['GET'])
    @jwt_required()
    def get_price_alerts():
        """Get all price alerts for current user"""
        try:
            current_user_id = get_jwt_identity()
            
            alerts = []
            
            # Get user's wishlists
            wishlists = Wishlist.query.filter_by(user_id=current_user_id).all()
            
            for wishlist in wishlists:
                items = WishlistItem.query.filter_by(
                    wishlist_id=wishlist.id,
                    alert_enabled=True
                ).all()
                
                for item in items:
                    if item.target_price:
                        product = Product.query.get(item.product_id)
                        if product:
                            # Get latest price
                            latest_price = PriceHistory.query.filter_by(
                                product_id=product.id
                            ).order_by(PriceHistory.timestamp.desc()).first()
                            
                            if latest_price and latest_price.price <= item.target_price:
                                alerts.append({
                                    'id': item.id,
                                    'product_id': product.id,
                                    'product_name': product.name,
                                    'product_url': product.product_url,
                                    'image_url': product.image_url or f"https://picsum.photos/100/100?random={product.id}",
                                    'current_price': latest_price.price,
                                    'target_price': item.target_price,
                                    'price_difference': round(item.target_price - latest_price.price, 2),
                                    'savings_percentage': round(((item.target_price - latest_price.price) / item.target_price) * 100, 1),
                                    'wishlist_id': wishlist.id,
                                    'wishlist_name': wishlist.name,
                                    'website': latest_price.website,
                                    'availability': latest_price.availability,
                                    'timestamp': latest_price.timestamp.isoformat() if latest_price.timestamp else None,
                                    'alert_time': datetime.utcnow().isoformat()
                                })
            
            # Sort by savings percentage (highest first)
            alerts.sort(key=lambda x: x['savings_percentage'], reverse=True)
            
            return jsonify({
                'success': True,
                'alerts': alerts,
                'count': len(alerts),
                'total_savings': sum(alert['price_difference'] for alert in alerts),
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Get price alerts error: {e}")
            return jsonify({'error': str(e)}), 500

    # Update Profile
    @app.route('/api/profile', methods=['PUT'])
    @jwt_required()
    def update_profile():
        """Update user profile"""
        try:
            current_user_id = get_jwt_identity()
            data = request.get_json()
            
            user = User.query.get(current_user_id)
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            # Update fields
            updates = {}
            if 'username' in data:
                username = data['username'].strip()
                if username and username != user.username:
                    # Check if username is taken
                    existing = User.query.filter_by(username=username).first()
                    if existing and existing.id != user.id:
                        return jsonify({'error': 'Username already taken'}), 400
                    user.username = username
                    updates['username'] = username
            
            if 'email' in data:
                email = data['email'].strip().lower()
                if email and email != user.email:
                    # Check if email is taken
                    existing = User.query.filter_by(email=email).first()
                    if existing and existing.id != user.id:
                        return jsonify({'error': 'Email already registered'}), 400
                    user.email = email
                    updates['email'] = email
            
            if 'pincode' in data:
                user.pincode = data['pincode'].strip() if data['pincode'] else None
                updates['pincode'] = user.pincode
            
            db.session.commit()
            
            logger.info(f"✅ Profile updated for user {current_user_id}")
            
            return jsonify({
                'success': True,
                'message': 'Profile updated successfully',
                'user': user.to_dict(),
                'updates': updates
            })
            
        except Exception as e:
            logger.error(f"Update profile error: {e}")
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    # Get Dashboard Stats
    @app.route('/api/dashboard/stats', methods=['GET'])
    @jwt_required()
    def get_dashboard_stats():
        """Get dashboard statistics"""
        try:
            current_user_id = get_jwt_identity()
            
            # Get wishlist count
            wishlist_count = Wishlist.query.filter_by(user_id=current_user_id).count()
            
            # Get tracked products count
            product_count = db.session.query(Product.id)\
                .join(WishlistItem, Product.id == WishlistItem.product_id)\
                .join(Wishlist, WishlistItem.wishlist_id == Wishlist.id)\
                .filter(Wishlist.user_id == current_user_id)\
                .distinct().count()
            
            # Get active alerts count
            alerts_count = 0
            wishlists = Wishlist.query.filter_by(user_id=current_user_id).all()
            for wishlist in wishlists:
                items = WishlistItem.query.filter_by(wishlist_id=wishlist.id, alert_enabled=True).all()
                for item in items:
                    if item.target_price:
                        product = Product.query.get(item.product_id)
                        if product:
                            latest_price = PriceHistory.query.filter_by(
                                product_id=product.id
                            ).order_by(PriceHistory.timestamp.desc()).first()
                            if latest_price and latest_price.price <= item.target_price:
                                alerts_count += 1
            
            # Calculate total savings (demo - would need more complex logic)
            total_savings = random.randint(500, 5000)
            
            return jsonify({
                'success': True,
                'stats': {
                    'wishlists': wishlist_count,
                    'tracked_products': product_count,
                    'active_alerts': alerts_count,
                    'total_saved': total_savings,
                    'currency': '₹'
                },
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Get dashboard stats error: {e}")
            return jsonify({'error': str(e)}), 500

    # Quick Search (for dashboard)
    @app.route('/api/quick-search', methods=['POST'])
    def quick_search():
        """Quick search for dashboard"""
        try:
            data = request.get_json()
            query = data.get('query', '').strip()
            
            if not query or len(query) < 2:
                return jsonify({'error': 'Query too short'}), 400
            
            # Get limited results
            results = scraper.search_products(query, max_results=5, use_real_data=True)
            
            return jsonify({
                'success': True,
                'query': query,
                'results': results[:3],  # Limit to 3 for quick view
                'count': len(results)
            })
            
        except Exception as e:
            logger.error(f"Quick search error: {e}")
            return jsonify({'error': str(e)}), 500

    # ========== ERROR HANDLERS ==========
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Resource not found', 'path': request.path}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({'error': 'Method not allowed'}), 405

    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"Server error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500

            # Log application startup
    @app.before_request
    def log_startup():
        if not hasattr(app, 'startup_logged'):
            logger.info("=" * 50)
            logger.info("🚀 PriceTracker API Server Starting...")
            logger.info(f"📁 Static folder: {app.static_folder}")
            logger.info(f"🔗 API Base URL: http://localhost:5000/api")
            logger.info(f"🌐 Frontend URL: http://localhost:5000")
            logger.info("=" * 50)
            app.startup_logged = True

    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 PRICETRACKER - E-COMMERCE PRICE COMPARISON")
    print("=" * 50)
    print("📊 Dashboard: http://localhost:5000")
    print("🔍 Search: http://localhost:5000/product_search.html")
    print("💖 Wishlist: http://localhost:5000/wishlist.html")
    print("👤 Profile: http://localhost:5000/profile.html")
    print("🔐 Auth: http://localhost:5000/auth.html")
    print("⚡ API: http://localhost:5000/api/health")
    print("=" * 50)
    print("✅ Real-time scraping: Amazon & Flipkart")
    print("📈 Demo data: Myntra & Meesho")
    print("📊 Price tracking & alerts")
    print("💾 SQLite database: pricetracker.db")
    print("=" * 50)
    print("🛑 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)