from email.message import EmailMessage
from email.mime.text import MIMEText
import os
import smtplib
import string
from flask import Flask, flash, redirect, render_template, request, session, url_for, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from flask_mail import Mail, Message  # <-- Add this import
import db
from datetime import datetime
import random
from db import log_error_to_db

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Replace with a secure random key in production

# Flask-Mail configuration
app.config['MAIL_SERVER'] = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('SMTP_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('EMAIL_SENDER', 'time2orderofficial@gmail.com')
app.config['MAIL_PASSWORD'] = os.getenv('EMAIL_PASSWORD', 'yrwk fpff onmw enyj')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('EMAIL_SENDER', 'time2orderofficial@gmail.com')

mail = Mail(app)

@app.errorhandler(Exception)
def handle_error(error):
    # Clean error message (don’t show to user)
    error_message = str(error)
    url_path = request.path
    user_agent = request.headers.get('User-Agent')

    # Save error silently
    log_error_to_db(error_message, url_path, user_agent)

    # Render user-friendly error page
    return render_template('error.html'), 500

@app.route('/')
def home():
    show_modal = request.args.get('show_modal', None)
    default_pincode = '632009'
    is_logged_in = 'user_id' in session
    username = None
    if is_logged_in:
        user = db.get_user_by_id(session['user_id'])
        username = user['username'] if user else None
        default_pincode = user.get('pincode', default_pincode)
    shops = db.get_shops_by_pincode(default_pincode)
    return render_template('index.html', shops=shops, pincode=default_pincode, is_logged_in=is_logged_in, username=username,show_modal=show_modal)

 # function to open privacy_policy
@app.route('/privacy_policy')
def privacy_policy():
    return render_template('privacy_policy.html')
   
@app.route('/login', methods=['GET', 'POST'])
def login():
    print("Login endpoint reached")
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = db.get_user_by_username(username)
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['user_id']
            flash("Login successful!", 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'error')
            return redirect(url_for('home', show_modal='login'))
    return redirect(url_for('home', show_modal='login'))
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form['email']
        user = db.get_user_by_email(email)
        if user:
            otp = str(random.randint(100000, 999999))
            db.save_password_reset_otp(user['user_id'], otp)
        
            send_reset_otp_email(email, otp)
            session['reset_user_id'] = user['user_id']
            flash("A 6-digit code has been sent to your email.", 'success')
            return redirect(url_for('reset_password_verify'))
        else:
            flash("Email not found.", 'error')
            return redirect(url_for('reset_password'))
    return render_template('reset_password.html')

@app.route('/reset_password_verify', methods=['GET', 'POST'])
def reset_password_verify():
    if 'reset_user_id' not in session:
        flash("Session expired. Please try again.", 'error')
        return redirect(url_for('reset_password'))
    if request.method == 'POST':
        otp = request.form['otp']
        user_id = session['reset_user_id']
        if db.verify_password_reset_otp(user_id, otp):
            session['otp_verified'] = True
            return redirect(url_for('reset_password_change'))
        else:
            flash("Invalid code. Please try again.", 'error')
            return redirect(url_for('reset_password_verify'))
    return render_template('index.html',show_modal='verify_otp')

@app.route('/reset_password_change', methods=['GET', 'POST'])
def reset_password_change():
    if 'reset_user_id' not in session or not session.get('otp_verified'):
        flash("Session expired. Please try again.", 'error')
        return redirect(url_for('reset_password'))
    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password != confirm_password:
            flash("Passwords do not match.", 'error')
            return redirect(url_for('reset_password_change'))
        hashed_password = generate_password_hash(password)
        user_id = session['reset_user_id']
        db.update_user_password(user_id, hashed_password)
        session.pop('reset_user_id', None)
        session.pop('otp_verified', None)
        flash("Password reset successful. Please log in.", 'success')
        return redirect(url_for('login'))
    return render_template('index.html', show_modal='change_password')

def send_reset_otp_email(email, otp):
    try:
        sender_email = os.getenv('EMAIL_SENDER')
        sender_password = os.getenv('EMAIL_PASSWORD')
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', 587))
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f4;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    max-width: 600px;
                    margin: 20px auto;
                    background-color: #ffffff;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    text-align: center;
                    padding-bottom: 20px;
                }}
                .header h1 {{
                    color: #333333;
                    font-size: 24px;
                    margin: 0;
                }}
                .content {{
                    text-align: center;
                    color: #666666;
                    font-size: 16px;
                    line-height: 1.5;
                }}
                .otp {{
                    display: inline-block;
                    background-color: #007bff;
                    color: #ffffff;
                    font-size: 24px;
                    font-weight: bold;
                    padding: 10px 20px;
                    border-radius: 4px;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    color: #999999;
                    font-size: 14px;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Time2Order Password Reset</h1>
                </div>
                <div class="content">
                    <p>Your password reset code is:</p>
                    <div class="otp">{otp}</div>
                    <p>If you did not request this, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>© 2025 Time2Order. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        msg = EmailMessage()
        msg['Subject'] = 'Time2Order - Password Reset Code'
        msg['From'] = sender_email
        msg['To'] = email
        msg.set_content(html_content, subtype='html')

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
    except Exception as e:
        print(f"Failed to send reset OTP email: {str(e)}")
        flash("Failed to send email. Please try again later.", 'error')

# In-memory store for OTPs and verified emails (use a database in production)
otp_store = {}
verified_emails = {}

def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))

@app.route('/send_otp', methods=['POST'])

def send_otp():
    try:
        data = request.get_json()
        if not data or 'email' not in data:
            return jsonify({'error': 'Email is required in JSON payload'}), 400

        email = data['email'].strip()
        if not email:
            return jsonify({'error': 'Email cannot be empty'}), 400

        # ✅ Check if user already exists by email
        exists, field = db.check_user_exists(email=email)
        if exists:
            return jsonify({'error': f'{field.capitalize()} already exists.'}), 400

        # ✅ Generate OTP and store it
        otp = generate_otp()
        otp_store[email] = otp

        # ✅ Email configuration
        sender_email = "time2orderofficial@gmail.com"
        sender_password = "yrwk fpff onmw enyj"
        msg = MIMEText(f'Your OTP is: {otp}')
        msg['Subject'] = 'Email Verification OTP'
        msg['From'] = sender_email
        msg['To'] = email

        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(sender_email, sender_password)
                server.send_message(msg)
            return jsonify({'message': 'OTP sent'}), 200
        except Exception as e:
            app.logger.error(f'Failed to send OTP to {email}: {str(e)}')
            return jsonify({'error': f'Failed to send OTP: {str(e)}'}), 500

    except Exception as e:
        app.logger.error(f'Error in send_otp: {str(e)}')
        return jsonify({'error': 'Invalid request'}), 400


@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    try:
        data = request.get_json()
        if not data or 'email' not in data or 'otp' not in data:
            return jsonify({'error': 'Email and OTP are required in JSON payload'}), 400
        
        email = data['email'].strip()
        otp = data['otp'].strip()

        if not email or not otp:
            return jsonify({'error': 'Email and OTP cannot be empty'}), 400

        if otp_store.get(email) == otp:
            verified_emails[email] = True
            del otp_store[email]
            return jsonify({'message': 'OTP verified'}), 200
        return jsonify({'error': 'Invalid OTP'}), 400
    except Exception as e:
        app.logger.error(f'Error in verify_otp: {str(e)}')
        return jsonify({'error': 'Invalid request'}), 400
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            # Ensure all required fields are present
            required_fields = ['name', 'username', 'email', 'phone_number', 'password', 'confirm_password', 'address', 'postal_code']
            form_data = {}
            form_data['email'] = request.form.get('email', '').strip()
            if not form_data['email']:
                flash("Email is required.", 'error')
                return redirect(url_for('home', show_modal='signup'))
            for field in required_fields:
                value = request.form.get(field)
                if not value:
                    flash(f"Missing required field: {field.capitalize()}.", 'error')
                    return redirect(url_for('home', show_modal='signup'))
                form_data[field] = value.strip()
            form_data['alt_phone_number'] = request.form.get('alt_phone_number', '').strip() or None
            print(f"Form data received: {form_data}")
            
            # Check if email is verified
            if not verified_emails.get(form_data['email']):
                flash("Please verify your email first.", 'error')
                return redirect(url_for('home', show_modal='signup'))

            if form_data['password'] != form_data['confirm_password']:
                flash("Passwords do not match.", 'error')
                return redirect(url_for('home', show_modal='signup'))
            
            if db.check_username_exists(form_data['username']):
                flash("Username already exists.", 'error')
                return redirect(url_for('home', show_modal='signup'))
            
            hashed_password = generate_password_hash(form_data['password'])
            try:
                db.insert_user(
                    form_data['username'],
                    hashed_password,
                    form_data['phone_number'],
                    form_data['email'],
                    form_data['address'],
                    form_data['postal_code'],
                    form_data['name'],
                    form_data['alt_phone_number']
                )
                del verified_emails[form_data['email']]  # Clear verified email after successful registration
                flash("Registration successful! Please log in.", 'success')
                return redirect(url_for('home', show_modal='login'))
            except Exception as e:
                app.logger.error(f'Registration failed for {form_data["username"]}: {str(e)}')
                flash(f"Registration failed: {str(e)}.", 'error')
                return redirect(url_for('home', show_modal='signup'))
        except KeyError as e:
            missing_field = str(e).strip("'")
            app.logger.error(f'Missing form field: {missing_field}')
            flash(f"Missing required field: {missing_field.capitalize()}.", 'error')
            return redirect(url_for('home', show_modal='signup'))
        except Exception as e:
            app.logger.error(f'Error in register: {str(e)}')
            flash("An error occurred during registration. Please try again.", 'error')
            return redirect(url_for('home', show_modal='signup'))
    return redirect(url_for('home', show_modal='signup'))
@app.route('/terms')
def accept_terms():
    return render_template('terms.html')
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('cart', None)
    flash("You have been logged out.")
    return redirect(url_for('home'))

@app.route('/search', methods=['POST'])
def search_by_pincode():
    default_pincode = '600001'
    pincode = request.form.get('pincode') or default_pincode
    print(f"Searching shops by pincode: {pincode}")
    shops = db.get_shops_by_pincode(pincode)
    is_logged_in = 'user_id' in session
    username = None
    if is_logged_in:
        user = db.get_user_by_id(session['user_id'])
        username = user['username'] if user else None
        default_pincode = user.get('pincode', default_pincode)
    return render_template('index.html', shops=shops, pincode=pincode, is_logged_in=is_logged_in, username=username)


@app.route('/searchshop', methods=['GET'])
def search_shop():
    shop_name = request.args.get('shop_name', '')
    pincode = request.args.get('pincode', '600001')  # Get pincode from the HTML form or default to '600001'
    shops = db.get_shops_by_name(shop_name, pincode)  # Update the DB function to filter by pincode as well
    
    is_logged_in = 'user_id' in session
    username = None
    
    if is_logged_in:
        user = db.get_user_by_id(session['user_id'])
        username = user['username'] if user else None

    return render_template('index.html', shops=shops, pincode=pincode, is_logged_in=is_logged_in, username=username)

@app.route("/shop/<int:vendor_id>")
def shop_products(vendor_id):
    conn = None
    try:
        conn = db.get_connection()
        if not conn:
            return "Database connection failed", 500
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM vendors WHERE id = %s", (vendor_id,))
        shop = cursor.fetchone()
        if not shop:
            return "Shop not found", 404
        cursor.execute("SELECT * FROM products WHERE vendor_id = %s", (vendor_id,))
        products = cursor.fetchall()
        return render_template("shop_products.html", shop=shop, products=products)
    except Exception as e:
        print(f"Error in shop_products: {str(e)}")
        return "An error occurred", 500
    finally:
        if conn:
            cursor.close()
            conn.close()

@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    if 'cart' not in session:
        session['cart'] = []
    product_id_str = request.form.get('product_id', '').strip()
    vendor_id = request.form.get('vendor_id', '').strip()
    product_measure = request.form.get('product_measure', '').strip()
    quantity_str = request.form.get('quantity', '1').strip()
    if not product_id_str.isdigit() or not quantity_str.isdigit():
        flash("Invalid product ID or quantity.")
        return redirect(url_for('shop_products', vendor_id=vendor_id))
    product_id = int(product_id_str)
    quantity = int(quantity_str)
    item = {
        'product_id': product_id,
        'product_measure': product_measure,
        'quantity': quantity
    }
    item_exists = False
    for cart_item in session['cart']:
        if cart_item['product_id'] == product_id and cart_item['product_measure'] == product_measure:
            cart_item['quantity'] += quantity
            item_exists = True
            break
    if not item_exists:
        session['cart'].append(item)
    session.modified = True
    flash("Product added to cart!")
    return redirect(url_for('shop_products', vendor_id=vendor_id))

@app.route('/update-cart-quantity', methods=['POST'])
def update_cart_quantity():
    if 'cart' not in session or not session['cart']:
        return jsonify({'success': False, 'message': 'Cart is empty.'}), 400

    product_id = request.form.get('product_id')
    product_measure = request.form.get('product_measure')
    change = request.form.get('change')

    try:
        product_id = int(product_id)
        change = int(change)
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'Invalid input.'}), 400

    cart_updated = False
    new_quantity = 0
    subtotal = 0
    total = 0

    # Find and update the cart item
    for item in session['cart']:
        if item['product_id'] == product_id and item['product_measure'] == product_measure:
            new_quantity = item['quantity'] + change
            if new_quantity <= 0:
                session['cart'].remove(item)  # Remove item if quantity becomes 0
            else:
                item['quantity'] = new_quantity
            cart_updated = True
            break

    if not cart_updated:
        return jsonify({'success': False, 'message': 'Item not found in cart.'}), 404

    # Recalculate cart totals
    product_ids = [item['product_id'] for item in session['cart'] if isinstance(item, dict) and 'product_id' in item]
    products_data = db.get_products_by_id(product_ids)
    products_dict = {product['id']: product for product in products_data}

    total = 0
    cart_display = []
    for item in session['cart']:
        if not isinstance(item, dict) or 'product_id' not in item:
            continue
        product = products_dict.get(item['product_id'])
        if product:
            quantity = int(item.get('quantity', 1))
            item_subtotal = float(product['product_price']) * quantity
            total += item_subtotal
            cart_display.append({
                'product_id': item['product_id'],
                'product_name': product['product_name'],
                'product_price': product['product_price'],
                'product_measure': item.get('product_measure', 'N/A'),
                'quantity': quantity,
                'subtotal': item_subtotal,
                'availability': product['availability'],
                'product_image': product.get('product_image', '/static/default.jpg')
            })
            if item['product_id'] == product_id and item['product_measure'] == product_measure:
                subtotal = item_subtotal if new_quantity > 0 else 0

    session.modified = True

    return jsonify({
        'success': True,
        'quantity': new_quantity,
        'subtotal': subtotal,
        'total': total,
        'remove': new_quantity <= 0
    })

@app.route('/view_cart')
def view_cart():
    if 'user_id' not in session:
        flash("Please log in to view your cart.")
        return redirect(url_for('login'))
    cart_items = session.get('cart', [])
    if not cart_items:
        return render_template('view_cart.html', products=[], total=0)
    product_ids = [item.get('product_id') for item in cart_items if isinstance(item, dict) and 'product_id' in item]
    products_data = db.get_products_by_id(product_ids)
    products_dict = {product['id']: product for product in products_data}
    cart_display = []
    total = 0
    for item in cart_items:
        if not isinstance(item, dict) or 'product_id' not in item:
            continue
        product_id = item['product_id']
        product = products_dict.get(product_id)
        if product:
            measure = item.get('product_measure', 'N/A')
            quantity = int(item.get('quantity', 1))
            subtotal = float(product['product_price']) * quantity
            total += subtotal
            cart_display.append({
                'product_id': product_id,
                'product_name': product['product_name'],
                'product_price': product['product_price'],
                'product_measure': measure,
                'quantity': quantity,
                'subtotal': subtotal,
                'availability': product['availability'],
                'product_image': product.get('product_image', '/static/default.jpg')
            })
    return render_template('view_cart.html', products=cart_display, total=total)
@app.route('/place-order', methods=['POST'])
def place_order():
    cart_items = session.get('cart', [])
    user_id = session.get('user_id')
    picking_time = request.form.get('picking_time')
    print(f"Picking time received: {picking_time}")
    if not cart_items or not user_id or not picking_time:
        return jsonify({'success': False, 'message': 'Incomplete order data.'}), 400
    
    try:
        picking_time = datetime.strptime(picking_time, '%Y-%m-%dT%H:%M').strftime('%Y-%m-%d %H:%M:%S')
        print(f"Formatted picking time: {picking_time}")
    except ValueError as e:
        return jsonify({'success': False, 'message': f'Invalid picking time format: {str(e)}'}), 400

    try:
        # Group items by shop
        shop_items = {}
        product_ids = [item['product_id'] for item in cart_items]
        products_data = db.get_products_by_id(product_ids)
        products_dict = {product['id']: product for product in products_data}

        for item in cart_items:
            product = products_dict.get(item['product_id'])
            if not product:
                return jsonify({'success': False, 'message': f'Product ID {item["product_id"]} not found.'}), 404
            if not product['availability']:
                return jsonify({'success': False, 'message': f'Product {product["product_name"]} is not available.'}), 400
            shop_id = product['vendor_id']
            if shop_id not in shop_items:
                shop_items[shop_id] = []
            shop_items[shop_id].append({
                'product': product,
                'quantity': int(item.get('quantity', 1)),
                'measure': item.get('product_measure', 'N/A')
            })
        total_price = 0
        for shop_id, items in shop_items.items():
            for item in items:
                product = item['product']
                quantity = item['quantity']
                price = float(product['product_price'])
                total_price += price * quantity
        #check shop orders limit
        shop_ids = list(shop_items.keys())
        shop_orders_limit = db.get_shop_orders_limit(','.join(map(str, shop_ids)))
        print(f"Shop orders limit: {shop_orders_limit}")
        # Check minimum order quantity per shop
        shop_ids = list(shop_items.keys())
        minimum_items_by_shop = db.get_minimum_order_quantity(','.join(map(str, shop_ids)))

        # Verify that minimum_items_by_shop is a dictionary
        if not isinstance(minimum_items_by_shop, dict):
            print(f"Error: Expected dictionary from db.get_minimum_order_quantity, got {type(minimum_items_by_shop)}: {minimum_items_by_shop}")
            return jsonify({
                'success': False,
                'message': 'Invalid response from minimum order quantity check.'
            }), 500
                #increment the order count for each shop
        for shop_id in shop_ids:
            db.increment_order_count(shop_id)
        # Check minimum items for each shop
        for shop_id, items in shop_items.items():
            total_items_in_shop = len(items)
            min_items = minimum_items_by_shop.get(str(shop_id), 0)  # Default to 0 if shop_id not found
            if total_items_in_shop < int(min_items):
                return jsonify({
                    'success': False,
                    'message': f'Minimum {min_items} items required to place an order for shop_id: {shop_id}'
                }), 400
        #get remark from the form
        remark = request.form.get('remarks', '')
        # Create an order for each shop
        order_ids = []
        for shop_id, items in shop_items.items():
            order_id = db.insert_order(user_id, shop_id, picking_time,total_price, remark)
            if not order_id:
                return jsonify({'success': False, 'message': 'Failed to create order.'}), 500
            
            for item in items:
                product = item['product']
                quantity = item['quantity']
                price = float(product['product_price'])
                success = db.insert_order_item(order_id, shop_id, product['id'], quantity, price)
                if not success:
                    return jsonify({
                        'success': False,
                        'message': f'Failed to insert item for product_id: {product["id"]}'
                    }), 500
            order_ids.append(order_id)
        #change 24 hours to 12 hours
        picking_time = datetime.strptime(picking_time, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %I:%M %p')
        print(f"Formatted picking time for email: {picking_time}")
        # Send confirmation emails
        user = db.get_user_by_id(user_id)
        for shop_id, items in shop_items.items():
            shop = db.get_shop_by_id(shop_id)
            if shop and shop.get('email'):
                send_shop_confirmation_email(shop, items, picking_time, order_ids[-1], user)
            else:
                print(f"Warning: No email found for shop_id {shop_id}")
        
        if user and user.get('email'):
            send_user_confirmation_email(user, shop_items, picking_time, order_ids)
        else:
            print(f"Warning: No email found for user_id {user_id}")

        # Clear the cart
        session.pop('cart', None)
        return jsonify({
            'success': True,
            'message': 'Your order has been submitted successfully!',
            'redirect': url_for('orders')
        })

    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Something went wrong while placing the order: {str(e)}'
        }), 500

def send_user_confirmation_email(user, shop_items, picking_time, order_ids):
    try:
        sender_email = os.getenv('EMAIL_SENDER')
        sender_password = os.getenv('EMAIL_PASSWORD')
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', 587))

        msg = EmailMessage()
        msg['Subject'] = 'Time2Order - Your Order Confirmation'
        msg['From'] = sender_email
        msg['To'] = user['email']

        total_price = 0
        order_details = f"Dear {user.get('name', 'Customer')},\n\nThank you for your order at Time2Order! Below are the details of your order(s):\n\n"
        for shop_id, items in shop_items.items():
            shop = db.get_shop_by_id(shop_id)
            order_details += f"Order ID: {order_ids.pop(0)}\nShop: {shop.get('shop_name', 'Unknown Shop')}\nItems:\n"
            for item in items:
                product = item['product']
                quantity = item['quantity']
                price = float(product['product_price'])
                subtotal = price * quantity
                total_price += subtotal
                order_details += f"- {product['product_name']} (Qty: {quantity}, Measure: {item['measure']}) - ₹{subtotal:.2f}\n"
            order_details += "\n"
        order_details += f"Total Price: ₹{total_price:.2f}\nPicking Time: {picking_time}\n\n"
        order_details += "You can view your order details in your account at Time2Order.\n\nBest regards,\nThe Time2Order Team"

        msg.set_content(order_details)

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print(f"User confirmation email sent to {user['email']}")
    except Exception as e:
        print(f"Failed to send user confirmation email: {str(e)}")

def send_shop_confirmation_email(shop, items, picking_time, order_id, user):
    try:
        sender_email = os.getenv('EMAIL_SENDER')
        sender_password = os.getenv('EMAIL_PASSWORD')
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', 587))

        msg = EmailMessage()
        msg['Subject'] = f'Time2Order - New Order #{order_id}'
        msg['From'] = sender_email
        msg['To'] = shop['email']

        total_price = 0
        order_details = f"Dear {shop.get('name', 'Shop Owner')},\n\nYou have received a new order from {user.get('name', 'Customer')} at Time2Order. Below are the details:\n\n"
        order_details += f"Order ID: {order_id}\nCustomer: {user.get('name', 'N/A')} ({user.get('phone_number', 'N/A')})\nItems:\n"
        for item in items:
            product = item['product']
            quantity = item['quantity']
            price = float(product['product_price'])
            subtotal = price * quantity
            total_price += subtotal
            order_details += f"- {product['product_name']} (Qty: {quantity}, Measure: {item['measure']}) - ₹{subtotal:.2f}\n"
        order_details += f"\nTotal Price: ₹{total_price:.2f}\nPicking Time: {picking_time}\n\n"
        order_details += "Please prepare the order for the specified picking time.\n\nBest regards,\nThe Time2Order Team"

        msg.set_content(order_details)

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print(f"Shop confirmation email sent to {shop['email']}")
    except Exception as e:
        print(f"Failed to send shop confirmation email: {str(e)}")
        
        # Log the error but don't fail the order placement
@app.route('/order/<int:order_id>')
def view_order(order_id):
    if 'user_id' not in session:
        flash("Please log in to view your order.")
        return redirect(url_for('login'))
    order_details = db.get_order_details(order_id)
    if not order_details:
        flash("Order not found.")
        return redirect(url_for('home'))
    return render_template('order_details.html', order_details=order_details)


@app.route('/remove-from-cart', methods=['POST'])
def remove_from_cart():
    product_id = request.form.get('product_id')
    product_measure = request.form.get('product_measure')
    if product_id and product_measure and 'cart' in session:
        try:
            product_id = int(product_id)
            session['cart'] = [
                item for item in session['cart']
                if not (item['product_id'] == product_id and item['product_measure'] == product_measure)
            ]
            session.modified = True
            flash("Item removed from cart")
        except (ValueError, TypeError):
            flash("Invalid product ID or measure.")
    else:
        flash("Item could not be removed from cart.")
    return redirect(url_for('view_cart'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = db.get_user_by_id(session['user_id'])
    if not user:
        flash("User not found.")
        return redirect(url_for('login'))
    if request.method == 'POST':
        address = request.form['address']
        pincode = request.form['pincode']
        alt_phone_number = request.form.get('alt_phone_number', None)
        try:
            success = db.update_user(user['user_id'], user['email'], user['phone_number'], address, pincode, alt_phone_number)
            if success:
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'message': 'Failed to update profile.'})
        except Exception as e:
            return jsonify({'success': False, 'message': f'Error updating profile: {str(e)}'})
    return render_template('profile.html', user=user)
 

@app.route('/orders')
def orders():
    if 'user_id' not in session:
        flash("Please log in to view your orders.")
        return redirect(url_for('login'))
    orders = db.get_user_orders(session['user_id'])
    return render_template('orders.html', orders=orders)

@app.route('/about')
def about():
    return render_template('about.html')

# Route for contact form
# Route for contact form
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        try:
            name = request.form['name']
            email = request.form['email']
            subject = request.form['subject']
            message = request.form['message']

            # Prepare email
            msg = Message(
                subject=f"Contact Form Submission: {subject}",
                sender=app.config['MAIL_DEFAULT_SENDER'],
                recipients=['info@time2due.com'],
                body=f"""
                New Contact Form Submission

                Name: {name}
                Email: {email}
                Subject: {subject}
                Message: {message}
                """
            )

            # Send email
            mail.send(msg)

            # Optionally store in database (uncomment if needed)
            # contact_entry = ContactSubmission(name=name, email=email, subject=subject, message=message)
            # db.session.add(contact_entry)
            # db.session.commit()

            return jsonify({'status': 'success', 'message': 'Message sent successfully'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    return render_template('contact.html')

if __name__ == '__main__':
    app.run(debug=True)  # Enable debug mode for development