 # app.py

import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from config import Config
from models import db, User, Kantin, Menu, Order, OrderItem, Rating
from datetime import datetime, timedelta

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Fungsi untuk membuat tabel database dan mengisi data dummy
def create_tables():
    with app.app_context():
        # Dapatkan nama file database dari konfigurasi
        db_file_name = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        # Bangun path lengkap ke file database
        db_path = os.path.join(app.root_path, db_file_name)

        # Cek apakah file database sudah ada
        if not os.path.exists(db_path):
            print(f"Database {db_file_name} tidak ditemukan. Membuat database dan mengisi data dummy...")
            db.create_all() # Buat semua tabel yang didefinisikan di models.py
            
            # Masukkan data dummy HANYA JIKA DATABASE BARU DIBUAT
            if not User.query.first(): # Cek apakah tabel User kosong
                print("Mengisi data dummy...")
                
                # Buat user admin
                admin_user = User(username='admin', email='admin@foodcourt.com', role='admin')
                admin_user.set_password('admin123')
                db.session.add(admin_user)

                # Buat user kantin pertama
                kantin_user_a = User(username='kantin1', email='kantin1@foodcourt.com', role='kantin')
                kantin_user_a.set_password('kantin123')
                db.session.add(kantin_user_a)

                # Buat user kantin kedua
                kantin_user_b = User(username='kantin2', email='kantin2@foodcourt.com', role='kantin')
                kantin_user_b.set_password('kantin234')
                db.session.add(kantin_user_b)
                db.session.commit() # Commit users dulu untuk mendapatkan ID mereka

                # Buat kantin dan kaitkan dengan user_id yang sesuai
                kantin_a = Kantin(name='Kantin Enak', location='Blok A', last_order_at=datetime.utcnow() - timedelta(days=7), user_id=kantin_user_a.id) # DIEDIT
                kantin_b = Kantin(name='Warung Gaul', location='Blok B', last_order_at=datetime.utcnow(), user_id=kantin_user_b.id) # DIEDIT
                db.session.add_all([kantin_a, kantin_b])
                db.session.commit() # Commit lagi setelah menambahkan kantin

                # Buat menu dengan path gambar lokal
                menu1 = Menu(name='Nasi Goreng Spesial', description='Nasi goreng dengan telur dan ayam.', price=20000, stock=15, kantin=kantin_a, image_url='images/nasi_goreng.jpg')
                menu2 = Menu(name='Mie Ayam Bakso', description='Mie ayam dengan bakso dan pangsit.', price=18000, stock=10, kantin=kantin_a, image_url='images/mie_ayam.jpg')
                menu3 = Menu(name='Ayam Geprek', description='Ayam goreng krispi dengan sambal pedas.', price=25000, stock=20, kantin=kantin_b, image_url='images/ayam_geprek.jpg')
                menu4 = Menu(name='Es Jeruk', description='Minuman jeruk segar.', price=8000, stock=30, kantin=kantin_b, image_url='images/es_jeruk.jpg')
                db.session.add_all([menu1, menu2, menu3, menu4])
                db.session.commit()
                print("Data dummy berhasil dibuat!")
            else:
                print("Database sudah ada dan berisi data. Tidak membuat data dummy baru.")
        else:
            print(f"Database {db_file_name} sudah ditemukan. Tidak membuat ulang.")


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role', 'customer') 

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username sudah ada. Coba yang lain.', 'danger')
            return redirect(url_for('register'))

        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('Email sudah terdaftar. Coba yang lain.', 'danger')
            return redirect(url_for('register'))

        new_user = User(username=username, email=email, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registrasi berhasil! Silakan login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash(f'Selamat datang, {user.username}!', 'success')
            if user.role == 'admin' or user.role == 'kantin':
                return redirect(url_for('dashboard'))
            return redirect(url_for('menu_list'))
        else:
            flash('Username atau password salah.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('role', None)
    flash('Anda telah logout.', 'info')
    return redirect(url_for('index'))

@app.route('/menu')
def menu_list():
    query = request.args.get('q') # Ambil query pencarian
    
    if query:
        # Lakukan pencarian berdasarkan nama atau deskripsi
        menus = Menu.query.filter(
            (Menu.name.ilike(f'%{query}%')) | 
            (Menu.description.ilike(f'%{query}%'))
        ).all()
        flash(f"Menampilkan hasil pencarian untuk '{query}'.", 'info')
    else:
        menus = Menu.query.all()
    
    return render_template('menu.html', menus=menus)

@app.route('/add_to_cart/<int:menu_id>', methods=['POST'])
def add_to_cart(menu_id):
    if 'user_id' not in session:
        flash('Anda harus login untuk menambahkan item ke keranjang.', 'warning')
        return redirect(url_for('login'))

    menu = Menu.query.get_or_404(menu_id)
    quantity = int(request.form.get('quantity', 1))

    if quantity <= 0:
        flash('Kuantitas harus lebih dari 0.', 'danger')
        return redirect(url_for('menu_list'))

    if menu.stock < quantity:
        flash(f'Stok {menu.name} tidak mencukupi. Tersedia {menu.stock} item.', 'danger')
        return redirect(url_for('menu_list'))

    if 'cart' not in session:
        session['cart'] = {}

    cart = session['cart']
    menu_id_str = str(menu_id)

    if menu_id_str in cart:
        cart[menu_id_str]['quantity'] += quantity
    else:
        cart[menu_id_str] = {
            'name': menu.name,
            'price': menu.price,
            'quantity': quantity,
            'image_url': menu.image_url # Simpan path gambar di keranjang
        }
    session['cart'] = cart # Update session
    flash(f'{quantity}x {menu.name} ditambahkan ke keranjang!', 'success')
    return redirect(url_for('menu_list'))

@app.route('/cart')
def cart():
    if 'cart' not in session or not session['cart']:
        flash('Keranjang Anda kosong.', 'info')
        return render_template('cart.html', cart_items={}, total_price=0)

    cart_items = session['cart']
    total_price = sum(item['price'] * item['quantity'] for item in cart_items.values())
    return render_template('cart.html', cart_items=cart_items, total_price=total_price)

@app.route('/update_cart/<int:menu_id>', methods=['POST'])
def update_cart(menu_id):
    if 'user_id' not in session:
        flash('Anda harus login untuk mengelola keranjang.', 'warning')
        return redirect(url_for('login'))

    quantity = int(request.form.get('quantity', 0))
    menu_id_str = str(menu_id)
    cart = session.get('cart', {})

    if quantity <= 0:
        if menu_id_str in cart:
            del cart[menu_id_str]
            flash('Item dihapus dari keranjang.', 'info')
    else:
        menu = Menu.query.get_or_404(menu_id)
        if menu.stock < quantity:
            flash(f'Stok {menu.name} tidak mencukupi. Tersedia {menu.stock} item.', 'danger')
            return redirect(url_for('cart'))
        if menu_id_str in cart:
            cart[menu_id_str]['quantity'] = quantity
            flash('Kuantitas item diperbarui.', 'success')
        else:
            flash('Item tidak ditemukan di keranjang.', 'danger') 

    session['cart'] = cart
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'user_id' not in session:
        flash('Anda harus login untuk checkout.', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']
    cart_items = session.get('cart', {})

    if not cart_items:
        flash('Keranjang Anda kosong. Tidak bisa checkout.', 'danger')
        return redirect(url_for('menu_list'))

    total_price = sum(item['price'] * item['quantity'] for item in cart_items.values())

    if request.method == 'POST':
        try:
            new_order = Order(user_id=user_id, total_price=total_price, status='completed')
            db.session.add(new_order)
            db.session.commit() 

            kantin_ids_involved = set() # Set untuk melacak kantin yang terlibat dalam pesanan ini

            for menu_id_str, item_data in cart_items.items():
                menu_id = int(menu_id_str)
                menu = Menu.query.get(menu_id)
                if menu:
                    order_item = OrderItem(
                        order_id=new_order.id,
                        menu_id=menu_id,
                        quantity=item_data['quantity'],
                        price=item_data['price']
                    )
                    menu.stock -= item_data['quantity']
                    db.session.add(order_item)
                    kantin_ids_involved.add(menu.kantin_id) # Tambahkan ID kantin ke set

            db.session.commit()

            # Perbarui last_order_at untuk kantin yang terlibat
            for k_id in kantin_ids_involved:
                kantin = Kantin.query.get(k_id)
                if kantin:
                    kantin.last_order_at = datetime.utcnow() # Set waktu pesanan terakhir ke sekarang
                    db.session.add(kantin)
            db.session.commit()


            session.pop('cart', None) 
            flash('Pembayaran berhasil dan pesanan Anda telah ditempatkan! Silakan ambil makanan Anda.', 'success')
            return redirect(url_for('index'))

        except Exception as e:
            db.session.rollback() 
            flash(f'Terjadi kesalahan saat checkout: {str(e)}', 'danger')
            return redirect(url_for('cart'))

    return render_template('checkout.html', cart_items=cart_items, total_price=total_price)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session or (session['role'] != 'admin' and session['role'] != 'kantin'):
        flash('Anda tidak memiliki akses ke dashboard ini.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    current_user = User.query.get(user_id)

    if session['role'] == 'admin':
        all_orders = Order.query.order_by(Order.order_date.desc()).all()
        all_kantin = Kantin.query.all()
        total_revenue = db.session.query(db.func.sum(Order.total_price)).scalar() or 0
        return render_template('dashboard.html', orders=all_orders, kantin_list=all_kantin, total_revenue=total_revenue, role='admin')

    elif session['role'] == 'kantin':
        # MENGUBAH INI: Mencari kantin yang dikelola oleh user yang sedang login
        kantin = Kantin.query.filter_by(user_id=user_id).first() 
        
        if not kantin:
            flash('Anda belum terkait dengan kantin mana pun. Harap hubungi admin.', 'warning')
            return redirect(url_for('index'))

        kantin_menus = Menu.query.filter_by(kantin_id=kantin.id).all()
        
        # Ambil semua order items yang terkait dengan kantin ini
        kantin_order_items_raw = db.session.query(OrderItem, Order).join(Order).join(Menu).filter(Menu.kantin_id == kantin.id).order_by(Order.order_date.desc()).all()
        
        kantin_order_items = kantin_order_items_raw

        kantin_revenue = 0
        total_items_sold = 0 
        for item, order in kantin_order_items:
            kantin_revenue += item.quantity * item.price
            total_items_sold += item.quantity

        # Logika Notifikasi Pesanan Baru
        threshold_time = datetime.utcnow() - timedelta(minutes=5)
        new_orders = db.session.query(Order).join(OrderItem).join(Menu).filter(
            Menu.kantin_id == kantin.id,
            Order.order_date > threshold_time,
            Order.status == 'completed' 
        ).distinct().count() 

        new_orders_count = new_orders

        return render_template('dashboard.html', kantin=kantin, menus=kantin_menus,
                               kantin_order_items=kantin_order_items, kantin_revenue=kantin_revenue,
                               total_items_sold=total_items_sold, role='kantin',
                               new_orders_count=new_orders_count) 

    return redirect(url_for('index'))


@app.route('/admin/stock', methods=['GET', 'POST'])
def manage_stock():
    if 'user_id' not in session or session['role'] not in ['admin', 'kantin']:
        flash('Anda tidak memiliki akses ke halaman ini.', 'danger')
        return redirect(url_for('login'))

    kantin_menus = []
    current_kantin = None
    if session['role'] == 'admin':
        kantin_menus = Menu.query.all()
    elif session['role'] == 'kantin':
        # MENGUBAH INI: Mendapatkan kantin yang dikelola oleh user yang sedang login
        current_kantin = Kantin.query.filter_by(user_id=session['user_id']).first() 
        if current_kantin:
            kantin_menus = Menu.query.filter_by(kantin_id=current_kantin.id).all()
        else:
            flash('Anda belum terkait dengan kantin mana pun.', 'warning')
            return redirect(url_for('dashboard'))

    if request.method == 'POST':
        menu_id = request.form.get('menu_id')
        new_stock = request.form.get('stock')
        if not menu_id or new_stock is None: 
            flash('Menu ID dan Stok baru harus diisi.', 'danger')
            return redirect(url_for('manage_stock'))

        try:
            menu = Menu.query.get_or_404(menu_id)
            new_stock = int(new_stock)
            if new_stock < 0:
                flash('Stok tidak boleh kurang dari 0.', 'danger')
                return redirect(url_for('manage_stock'))

            # Validasi kantin pemilik
            if session['role'] == 'kantin' and menu.kantin_id != current_kantin.id: 
                 flash('Anda tidak punya izin mengubah stok menu ini.', 'danger')
                 return redirect(url_for('manage_stock'))

            menu.stock = new_stock
            db.session.commit()
            flash(f'Stok {menu.name} berhasil diperbarui menjadi {new_stock}.', 'success')
        except ValueError:
            flash('Stok harus berupa angka.', 'danger')
        except Exception as e:
            db.session.rollback() 
            flash(f'Terjadi kesalahan: {str(e)}', 'danger')
        return redirect(url_for('manage_stock'))

    return render_template('admin/stock.html', menus=kantin_menus)


# --- Rute Baru untuk Manajemen Menu Kantin ---
@app.route('/kantin/menus')
def manage_kantin_menus():
    if 'user_id' not in session or session['role'] != 'kantin':
        flash('Anda tidak memiliki akses ke halaman ini.', 'danger')
        return redirect(url_for('login'))

    # MENGUBAH INI: Mendapatkan kantin yang dikelola oleh user yang sedang login
    kantin = Kantin.query.filter_by(user_id=session['user_id']).first() 
    if not kantin:
        flash('Anda belum terkait dengan kantin mana pun. Harap hubungi admin.', 'warning')
        return redirect(url_for('dashboard'))
    
    menus = Menu.query.filter_by(kantin_id=kantin.id).all()
    return render_template('kantin/manage_menus.html', menus=menus)

@app.route('/kantin/menus/add', methods=['GET', 'POST'])
def add_menu():
    if 'user_id' not in session or session['role'] != 'kantin':
        flash('Anda tidak memiliki akses untuk menambah menu.', 'danger')
        return redirect(url_for('login'))

    # MENGUBAH INI: Mendapatkan kantin yang dikelola oleh user yang sedang login
    kantin = Kantin.query.filter_by(user_id=session['user_id']).first() 
    if not kantin:
        flash('Anda belum terkait dengan kantin mana pun. Harap hubungi admin.', 'warning')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        stock = int(request.form['stock'])
        image_url = request.form.get('image_url', 'images/placeholder.jpg') # Default placeholder

        # Validasi sederhana
        if not name or price <= 0 or stock < 0:
            flash('Nama, Harga (harus > 0), dan Stok (harus >= 0) harus valid.', 'danger')
            return render_template('kantin/menu_form.html')

        try:
            new_menu = Menu(
                name=name,
                description=description,
                price=price,
                stock=stock,
                kantin_id=kantin.id,
                image_url=image_url
            )
            db.session.add(new_menu)
            db.session.commit()
            flash(f'Menu "{name}" berhasil ditambahkan!', 'success')
            return redirect(url_for('manage_kantin_menus'))
        except Exception as e:
            db.session.rollback()
            flash(f'Terjadi kesalahan saat menambahkan menu: {str(e)}', 'danger')

    return render_template('kantin/menu_form.html')

@app.route('/kantin/menus/edit/<int:menu_id>', methods=['GET', 'POST'])
def edit_menu(menu_id):
    if 'user_id' not in session or session['role'] != 'kantin':
        flash('Anda tidak memiliki akses untuk mengedit menu.', 'danger')
        return redirect(url_for('login'))

    menu = Menu.query.get_or_404(menu_id)
    # MENGUBAH INI: Mendapatkan kantin yang dikelola oleh user yang sedang login
    kantin = Kantin.query.filter_by(user_id=session['user_id']).first() 
    
    # Pastikan user kantin hanya bisa mengedit menunya sendiri
    if not kantin or menu.kantin_id != kantin.id:
        flash('Anda tidak memiliki izin untuk mengedit menu ini.', 'danger')
        return redirect(url_for('manage_kantin_menus'))

    if request.method == 'POST':
        menu.name = request.form['name']
        menu.description = request.form['description']
        menu.price = float(request.form['price'])
        menu.stock = int(request.form['stock'])
        menu.image_url = request.form.get('image_url', menu.image_url)

        # Validasi sederhana
        if not menu.name or menu.price <= 0 or menu.stock < 0:
            flash('Nama, Harga (harus > 0), dan Stok (harus >= 0) harus valid.', 'danger')
            return render_template('kantin/menu_form.html', menu=menu)

        try:
            db.session.commit()
            flash(f'Menu "{menu.name}" berhasil diperbarui!', 'success')
            return redirect(url_for('manage_kantin_menus'))
        except Exception as e:
            db.session.rollback()
            flash(f'Terjadi kesalahan saat memperbarui menu: {str(e)}', 'danger')

    return render_template('kantin/menu_form.html', menu=menu)

@app.route('/kantin/menus/delete/<int:menu_id>', methods=['POST'])
def delete_menu(menu_id):
    if 'user_id' not in session or session['role'] != 'kantin':
        flash('Anda tidak memiliki akses untuk menghapus menu.', 'danger')
        return redirect(url_for('login'))

    menu = Menu.query.get_or_404(menu_id)
    # MENGUBAH INI: Mendapatkan kantin yang dikelola oleh user yang sedang login
    kantin = Kantin.query.filter_by(user_id=session['user_id']).first() 

    # Pastikan user kantin hanya bisa menghapus menunya sendiri
    if not kantin or menu.kantin_id != kantin.id:
        flash('Anda tidak memiliki izin untuk menghapus menu ini.', 'danger')
        return redirect(url_for('manage_kantin_menus'))
    
    try:
        db.session.delete(menu)
        db.session.commit()
        flash(f'Menu "{menu.name}" berhasil dihapus.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Terjadi kesalahan saat menghapus menu: {str(e)}', 'danger')
    
    return redirect(url_for('manage_kantin_menus'))


@app.route('/rate_menu/<int:menu_id>', methods=['POST'])
def rate_menu(menu_id):
    if 'user_id' not in session:
        flash('Anda harus login untuk memberikan rating.', 'warning')
        return redirect(url_for('login'))

    score = request.form.get('score')
    comment = request.form.get('comment', '')

    if not score or not (1 <= int(score) <= 5):
        flash('Rating harus antara 1 sampai 5.', 'danger')
        return redirect(url_for('menu_list')) 

    user_id = session['user_id']

    existing_rating = Rating.query.filter_by(user_id=user_id, menu_id=menu_id).first()
    if existing_rating:
        existing_rating.score = int(score)
        existing_rating.comment = comment
        existing_rating.rating_date = datetime.utcnow()
        flash('Rating Anda berhasil diperbarui!', 'success')
    else:
        new_rating = Rating(user_id=user_id, menu_id=menu_id, score=int(score), comment=comment)
        db.session.add(new_rating)
        flash('Terima kasih atas rating Anda!', 'success')

    db.session.commit()
    return redirect(url_for('menu_list')) 

# Blok utama untuk menjalankan aplikasi Flask
if __name__ == '__main__':
    create_tables() 
    app.run(debug=True)
