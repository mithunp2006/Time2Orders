import os
import mysql.connector
#load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

#function to insert the error message into the database
def log_error_to_db(error_message, url_path=None, user_agent=None):
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO error_logs (error_message, url_path, user_agent)
                VALUES (%s, %s, %s)
            """
            cursor.execute(sql, (error_message, url_path, user_agent))
            conn.commit()
    except Exception as e:
        print("Failed to log error:", e)
    finally:
        if 'conn' in locals():
            conn.close()
            
def get_connection():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "root"),
            database=os.getenv("DB_NAME", "Time2order")
        )
        return conn
    except mysql.connector.Error as e:
        print(f"Database connection failed: {e}")
        return None

def get_shops_by_pincode(pincode):
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT id,mobile_number,email,shop_name,shop_owner_name,map_link,category,shop_address,pincode,shop_status FROM vendors WHERE pincode = %s"
        cursor.execute(query, (pincode,))
        results = cursor.fetchall()
        conn.commit()
        return results
    except mysql.connector.Error as e:
        conn.rollback()
        print(f"Error fetching shops by pincode: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_user_pincode(user_id):
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT pincode FROM users WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        conn.commit()
        return result['pincode'] if result else None
    except mysql.connector.Error as e:
        conn.rollback()
        print(f"Error fetching user pincode: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_shops_by_name(shop_name, default_pincode=None):
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        if default_pincode:
            query = "SELECT id,mobile_number,email,shop_name,shop_owner_name,map_link,category,shop_address,pincode,shop_status FROM vendors WHERE shop_name LIKE %s AND pincode = %s"
            cursor.execute(query, ('%' + shop_name + '%', default_pincode))
        else:
            query = "SELECT id,mobile_number,email,shop_name,shop_owner_name,map_link,category,shop_address,pincode,shop_status FROM vendors WHERE shop_name LIKE %s"
            cursor.execute(query, ('%' + shop_name + '%',))
        results = cursor.fetchall()
        conn.commit()
        return results
    except mysql.connector.Error as e:
        conn.rollback()
        print(f"Error fetching shops by name: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_products_by_vendor(vendor_id):
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM products WHERE vendor_id = %s"
        cursor.execute(query, (vendor_id,))
        results = cursor.fetchall()
        conn.commit()
        return results
    except mysql.connector.Error as e:
        conn.rollback()
        print(f"Error fetching products by vendor: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_products_by_id(product_ids):
    if not product_ids:
        return []
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        placeholders = ','.join(['%s'] * len(product_ids))
        query = f"SELECT * FROM products WHERE id IN ({placeholders})"
        cursor.execute(query, tuple(product_ids))
        products = cursor.fetchall()
        conn.commit()
        return products
    except mysql.connector.Error as e:
        conn.rollback()
        print(f"Error fetching products by ID: {e}")
        return []
    finally:
        cursor.close()
        conn.close()
def insert_order(user_id, shop_id, picking_time,total_price, remark):
    conn = get_connection()
    if not conn:
        print("Database connection failed.")
        return None
    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO orders (user_id, shop_id, picking_time,total_price, remarks)
            VALUES (%s, %s, %s, %s,%s)
        """
        cursor.execute(query, (user_id, shop_id, picking_time, total_price,remark))
        conn.commit()
        order_id = cursor.lastrowid
        print(f"Order inserted successfully. Order ID: {order_id}")
        return order_id
    except mysql.connector.Error as e:
        conn.rollback()
        print(f"Error inserting order: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def insert_order_item(order_id, shop_id, product_id, quantity, price):
    conn = get_connection()
    if not conn:
        print("Database connection failed.")
        return False
    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO order_items (order_id, shop_id, product_id, quantity, price)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (order_id, shop_id, product_id, quantity, price))
        conn.commit()
        print(f"Order item inserted successfully. Order ID: {order_id}, Product ID: {product_id}")
        return True
    except mysql.connector.Error as e:
        conn.rollback()
        print(f"Error inserting order item: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def get_order_details(order_id):
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT oi.order_item_id, oi.order_id, oi.shop_id, p.product_name, p.product_price, oi.quantity, oi.price
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = %s
        """
        cursor.execute(query, (order_id,))
        details = cursor.fetchall()
        conn.commit()
        return details
    except mysql.connector.Error as e:
        conn.rollback()
        print(f"Error fetching order details: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def insert_user(username, hashed_password, phone_number, email, address, pincode, name, alt_phone_number):
    conn = get_connection()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO users (username, password, phone_number, email, address, pincode, name, alt_phone_number)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (username, hashed_password, phone_number, email, address, pincode, name, alt_phone_number))
        conn.commit()
    except mysql.connector.Error as e:
        conn.rollback()
        print(f"Error inserting user: {e}")
    finally:
        cursor.close()
        conn.close()

def check_username_exists(username):
    conn = get_connection()
    if not conn:
        return True
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT username FROM users WHERE username = %s"
        cursor.execute(query, (username,))
        user = cursor.fetchone()
        conn.commit()
        return user is not None
    except mysql.connector.Error as e:
        conn.rollback()
        print(f"Error checking username: {e}")
        return True
    finally:
        cursor.close()
        conn.close()

def check_user_exists(email):
    conn = get_connection()
    print(f"Checking user exists with email: {email}")
    if not conn:
        return True, "database"
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT email FROM users WHERE email = %s "
        cursor.execute(query, (email,))
        user = cursor.fetchone()
        print(f"User fetched: {user}")
        if user:
            if user.get('email') == email:
                return True, "email"
        return False, None
    except mysql.connector.Error as e:
        conn.rollback()
        print(f"Error checking user exists: {e}")
        return True, "database"
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()
#get_user_by_email
def get_user_by_email(email):
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT user_id FROM users WHERE email = %s"
        cursor.execute(query, (email,))
        user = cursor.fetchone()
        conn.commit()
        return user
    except mysql.connector.Error as e:
        conn.rollback()
        print(f"Error fetching user by email: {e}")
        return None
    finally:
        cursor.close()
        conn.close()
def get_user_by_username(username):
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM users WHERE username = %s OR email = %s"
        cursor.execute(query, (username,username))
        user = cursor.fetchone()
        conn.commit()
        return user
    except mysql.connector.Error as e:
        conn.rollback()
        print(f"Error fetching user by username: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_user_by_id(user_id):
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM users WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()
        conn.commit()
        return user
    except mysql.connector.Error as e:
        conn.rollback()
        print(f"Error fetching user by ID: {e}")
        return None
    finally:
        cursor.close()
        conn.close()
#verify_password_reset_otp(user_id, otp)
def verify_password_reset_otp(user_id, otp):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM password_reset_otp WHERE user_id = %s AND otp = %s"
        cursor.execute(query, (user_id, otp))
        result = cursor.fetchone()
        conn.commit()
        if result:
            return True
        else:
            return False
    except mysql.connector.Error as e:
        conn.rollback()
        print(f"Error verifying password reset OTP: {e}")
        return False
    finally:
        cursor.close()
        conn.close()
#save_password_reset_otp
def save_password_reset_otp(user_id, otp):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        query = "INSERT INTO password_reset_otp (user_id, otp, expires_at) VALUES (%s, %s, DATE_ADD(NOW(), INTERVAL 10 MINUTE))"
        cursor.execute(query, (user_id, otp))
        conn.commit()
        return True
    except mysql.connector.Error as e:
        conn.rollback()
        print(f"Error saving password reset OTP: {e}")
        return False
    finally:
        cursor.close()
        conn.close()
#update_password
def update_user_password(user_id, new_password):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        query = "UPDATE users SET password = %s WHERE user_id = %s"
        cursor.execute(query, (new_password, user_id))
        conn.commit()
        return True
    except mysql.connector.Error as e:
        conn.rollback()
        print(f"Error updating password: {e}")
        return False
    finally:
        cursor.close()
        conn.close()
def get_shop_by_id(shop_id):
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT id,mobile_number,email,shop_name,shop_owner_name,map_link,category,shop_address,pincode,shop_status FROM vendors WHERE id = %s"
        cursor.execute(query, (shop_id,))
        shop = cursor.fetchone()
        conn.commit()
        return shop
    except mysql.connector.Error as e:
        conn.rollback()
        print(f"Error fetching shop by ID: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_user_orders(user_id):
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT o.*, v.shop_name 
            FROM orders o 
            JOIN vendors v ON o.shop_id = v.id 
            WHERE o.user_id = %s
        """
        cursor.execute(query, (user_id,))
        orders = cursor.fetchall()
        conn.commit()
        return orders
    except mysql.connector.Error as e:
        conn.rollback()
        print(f"Error fetching user orders: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_vendor_orders(shop_id):
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT o.order_id, o.shop_id, o.picking_time, o.status, p.product_name, oi.quantity, oi.price
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            JOIN products p ON oi.product_id = p.id
            WHERE o.shop_id = %s AND o.status != 'cancelled'
        """
        cursor.execute(query, (shop_id,))
        orders = cursor.fetchall()
        conn.commit()
        return orders
    except mysql.connector.Error as e:
        conn.rollback()
        print(f"Error fetching vendor orders: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_minimum_order_quantity(shop_ids):
    conn = get_connection()
    if not conn:
        print("Error: Failed to get database connection")
        return {}
    try:
        cursor = conn.cursor(dictionary=True)
        if not shop_ids:
            print("Warning: Empty shop_ids provided")
            return {}
        id_list = [id.strip() for id in shop_ids.split(',') if id.strip()]
        if not id_list:
            print("Warning: No valid shop IDs after parsing")
            return {}
        placeholders = ','.join(['%s'] * len(id_list))
        query = f"SELECT id, minimum_order_quantity FROM vendors WHERE id IN ({placeholders})"
        cursor.execute(query, tuple(id_list))
        results = cursor.fetchall()
        result_dict = {str(row['id']): int(row['minimum_order_quantity']) for row in results}
        conn.commit()
        return result_dict
    except mysql.connector.Error as e:
        conn.rollback()
        print(f"Error in get_minimum_order_quantity: {e}")
        return {}
    finally:
        cursor.close()
        conn.close()
        
def update_user(user_id, email, phone_number, address, pincode, alt_phone_number):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        query = """
            UPDATE users 
            SET email = %s, phone_number = %s, address = %s, pincode = %s, alt_phone_number = %s
            WHERE user_id = %s
        """
        cursor.execute(query, (email, phone_number, address, pincode, alt_phone_number, user_id))
        conn.commit()
        return True
    except mysql.connector.Error as e:
        conn.rollback()
        print(f"Error updating user: {e}")
        return False
    finally:
        cursor.close()
        conn.close()
        
def increment_order_count(shop_id):
    conn = get_connection()
    if not conn:
        print("Error: Failed to get database connection")
        return False
    try:
        cursor = conn.cursor()
        query = "UPDATE subscriptions SET current_order_count = current_order_count + 1 WHERE vendor_id = %s"
        cursor.execute(query, (shop_id,))
        conn.commit()
        return True
    except mysql.connector.Error as e:
        conn.rollback()
        print(f"Error incrementing order count: {e}")
        return False
    finally:
        cursor.close()
        conn.close()
        
def get_shop_orders_limit(shop_id):
    conn = get_connection()
    if not conn:
        print("Error: Failed to get database connection")
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT current_order_count, order_limit FROM subscriptions WHERE vendor_id = %s"
        cursor.execute(query, (shop_id,))
        result = cursor.fetchone()
        conn.commit()
        return result
    except mysql.connector.Error as e:
        conn.rollback()
        print(f"Error fetching shop orders limit: {e}")
        return None
    finally:
        cursor.close()
        conn.close()
