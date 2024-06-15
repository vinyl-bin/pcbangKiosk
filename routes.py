from flask import Flask, render_template, redirect, url_for, request, session, jsonify, request
from models import db, Customer, Staff, Boss, Menu, SenderTypeForNotice, Notice, Message, SenderTypeForMessage, Order
import os
from datetime import datetime
import json
from enum import Enum

app = Flask(
    __name__,
    static_url_path=None,
    # static_folder='./templates/', ## 정적 폴더 위치, default로 index.html을 불러옴
)

# 이미지를 업로드할 디렉토리 설정
upload_folder = os.path.join(os.getcwd(), 'static/menu_images')
os.makedirs(upload_folder, exist_ok=True)

# 나머지 설정 추가
app.config['UPLOAD_FOLDER'] = upload_folder
app.config['SECRET_KEY'] = 'this is secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pcbang_kiosk.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


@app.route('/')
def index():
    return render_template("index.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form['role']
        user_id = request.form['id']
        password = request.form['pw']

        user = None
        if role == 'customer':
            user = Customer.query.filter_by(id=user_id, pw=password).first()
        elif role == 'staff':
            user = Staff.query.filter_by(id=user_id, pw=password).first()
        elif role == 'boss':
            user = Boss.query.filter_by(id=user_id, pw=password).first()

        if user:
            session['user_id'] = user_id
            session['role'] = role
            return redirect(url_for('dashboard'))
        else:
            return "Invalid credentials", 401
    return render_template('login.html')
    

@app.route('/signup', methods=['GET', 'POST'])
def register():
    
    if request.method == 'POST':
        role = request.form['role']
        user_id = request.form['id']
        password = request.form['pw']
        name = request.form['name']

        if role == 'customer':
            new_user = Customer(id=user_id, pw=password, name=name, chargeTime=None)
        elif role == 'staff':
            new_user = Staff(id=user_id, pw=password, name=name)
        elif role == 'boss':
            new_user = Boss(id=user_id, pw=password, name=name)
        else:
            return "Invalid role", 400

        db.session.add(new_user)
        db.session.commit()
    
        return redirect(url_for('login'))
    return render_template('signup.html')


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    role = session['role']
    if role == 'customer':
        return render_template('customer_dashboard2.html')
    elif role == 'staff':
        return render_template('staff_dashboard2.html')
    elif role == 'boss':
        return render_template('boss_dashboard2.html')
    else:
        return "Invalid role", 400

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('role', None)
    return redirect(url_for('index'))

# <!------- boss용 ----------!>

@app.route('/add_menu', methods=['GET', 'POST'])
def add_menu():
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        
        # 이미지 파일을 업로드하고 저장하는 코드
        if 'image' in request.files:
            image_file = request.files['image']
            image_url = upload_image(image_file)  # 이미지를 업로드하고 저장한 후 URL을 반환하는 함수 호출
        else:
            image_url = None

        # 메뉴 정보를 데이터베이스에 추가하는 코드
        new_menu = Menu(name=name, price=price, image_url=image_url)
        db.session.add(new_menu)
        db.session.commit()
        
        return redirect(url_for('dashboard'))  # 리디렉션 수행

    return render_template('add_menu.html')


# 이미지를 업로드하고 저장하는 함수
def upload_image(image_file):
    if image_file:
        filename = image_file.filename
        image_url = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image_file.save(image_url)
        
        return 'static/menu_images/' + filename
    else:
        return None



@app.route('/delete_menu/<int:menu_id>', methods=['DELETE'])
def delete_menu(menu_id):
    if session['role'] == 'boss':
        menu = Menu.query.get(menu_id)
        if menu:
            db.session.delete(menu)
            db.session.commit()
            return jsonify({'message': 'Menu deleted successfully'})
        else:
            return jsonify({'error': 'Menu not found'}), 404
    else:
        return "Unauthorized", 401





# <!----------- staff용 ------------!>

# 특정 사용자와의 메시지 스레드 가져오기
@app.route('/get_conversation_partners')
def get_conversation_partners():
    user_id = session.get('user_id')
    if session.get('role') == 'staff':
        role = SenderTypeForMessage.STAFF
    else:
        role = SenderTypeForMessage.CUSTOMER
    
    if not user_id or not role:
        return jsonify({'error': 'Unauthorized'}), 401

    # sender 또는 recipient로서의 메시지 가져오기
    sent_messages = Message.query.filter_by(sender_id=user_id, sender_type=role.name).all()
    received_messages = Message.query.filter_by(recipient_id=user_id, recipient_type=role.name).all()
    
    partners = set()

    # 상대방 정보 추출
    for message in sent_messages:
        partners.add((message.recipient_type.name, message.recipient_id))
    for message in received_messages:
        partners.add((message.sender_type.name, message.sender_id))
    
    # 결과를 JSON 형태로 반환
    partner_list = [{'type': p[0], 'id': p[1]} for p in partners]
    
    return jsonify(partner_list)


@app.route('/get_messages/<recipient_type>/<recipient_id>')
def get_messages(recipient_type, recipient_id):
    sender_id = session.get('user_id')
    
    if session.get('role') == 'staff':
        role = SenderTypeForMessage.STAFF
    else:
        role = SenderTypeForMessage.CUSTOMER
    
    messages = Message.query.filter(
        ((Message.sender_id == sender_id) & (Message.sender_type == role.name) & 
        (Message.recipient_id == recipient_id) & (Message.recipient_type == recipient_type))
        | 
        ((Message.sender_id == recipient_id) & (Message.sender_type == recipient_type) & 
        (Message.recipient_id == sender_id) & (Message.recipient_type == role.name))
    ).order_by(Message.sent_at).all()
    
    message_list = []
    for message in messages:
        message_data = {
            'message_id': message.message_id,
            'sender_type': message.sender_type.name,
            'sender_id': message.sender_id,
            'recipient_type': message.recipient_type.name,
            'recipient_id': message.recipient_id,
            'content': message.content,
            'sent_at': message.sent_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        message_list.append(message_data)
    return jsonify(message_list)


# API 엔드포인트 - 메시지 전송
@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.get_json()
    
    if data.get('recipient_type') == 'STAFF' or data.get('recipient_type') == 'staff':
        recipient_type = SenderTypeForMessage.STAFF
    else:
        recipient_type = SenderTypeForMessage.CUSTOMER
    
    recipient_id = data.get('recipient_id')
    content = data.get('content')
    
    if session['role'] == 'staff':
        sender_type = SenderTypeForMessage.STAFF
    else:
        sender_type = SenderTypeForMessage.CUSTOMER

    sender_id = session.get('user_id') 

    new_message = Message(
        sender_type=sender_type,
        sender_id=sender_id,
        recipient_type=recipient_type,
        recipient_id=recipient_id,
        content=content,
        sent_at=db.func.current_timestamp()
    )

    db.session.add(new_message)
    db.session.commit()

    return jsonify({
        'sender_type': new_message.sender_type.value,
        'sender_id': new_message.sender_id,
        'recipient_type': new_message.recipient_type.value,
        'recipient_id': new_message.recipient_id,
        'content': new_message.content,
        'sent_at': new_message.sent_at.strftime('%Y-%m-%d %H:%M:%S')
    })
    
# 메시지 스레드 페이지
@app.route('/message_thread/<recipient_type>/<recipient_id>')
def message_thread(recipient_type, recipient_id):
    return render_template('message2.html', recipient_type=recipient_type, recipient_id=recipient_id)






# <!----------- customer용 ------------!>

# 메뉴 주문 추가 페이지
@app.route('/pick_menu/<int:menu_id>', methods=['POST'])
def pick_menu(menu_id):
    
    customer_id = session.get('user_id')
    
    order = Order.query.filter_by(customer_id=customer_id, menu_id=menu_id).first()
    
    if order:
        order.quantity += 1
    else:
        order = Order(customer_id=customer_id, menu_id=menu_id, quantity=1)
        db.session.add(order)
   
    db.session.commit()
    return redirect(url_for('dashboard'))

# 메뉴 주문 취소 페이지
@app.route('/cancle_menu/<int:menu_id>', methods=['POST'])
def cancle_menu(menu_id):
    
    customer_id = session.get('user_id')
    
    order = Order.query.filter_by(customer_id=customer_id, menu_id=menu_id).first()
    
    if order:
        if order.quantity > 1:
            order.quantity -= 1
        else:
            db.session.delete(order)
        db.session.commit()
            
    return redirect(url_for('dashboard'))
   




# <!------------- 공용 ------------!>

# 공지사항 추가 페이지
@app.route('/add_notice', methods=['GET', 'POST'])
def add_notice():
    if request.method == 'POST':
        content = request.form['content']
        if session['role'] == 'staff':
            author_type = SenderTypeForNotice.STAFF
        else:
            author_type = SenderTypeForNotice.BOSS
        author_id = session.get('user_id') 
        current_time = datetime.now()
        new_notice = Notice(content=content, author_type=author_type, author_id=author_id, created_at=current_time)
        db.session.add(new_notice)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('add_notice.html')

# 모든 공지사항을 보여주는 페이지
@app.route('/get_notices', methods=['GET'])
def get_notices():
    notices = Notice.query.all()
    notice_list = []
    for notice in notices:
        notice_list.append({
            'notice_id': notice.notice_id,
            'content': notice.content,
            'created_at': notice.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'author_id': notice.author_id,
            'author_type' : notice.author_type.value
        })
    return jsonify(notice_list)

# 공지사항 삭제 기능
@app.route('/delete_notice/<int:notice_id>', methods=['DELETE'])
def delete_notice(notice_id):
    
    if session['role'] == 'boss':
        notice = Notice.query.get(notice_id)
        if notice:
            db.session.delete(notice)
            db.session.commit()
            return jsonify({'message': 'notice deleted successfully'})
        else:
            return jsonify({'error': 'notice not found'}), 404
        
    elif session['role'] == 'staff':
        notice = Notice.query.get(notice_id)
        if notice:
            db.session.delete(notice)
            db.session.commit()
            return jsonify({'message': 'notice deleted successfully'})
        else:
            return jsonify({'error': 'notice not found'}), 404
        
    else:
        return "Unauthorized", 401

# 메뉴 데이터 가져오기
@app.route('/get_menu')
def get_menu():
    # 메뉴 데이터를 데이터베이스에서 가져오는 코드
    menu_data = Menu.query.all()

    # 메뉴 데이터를 JSON 형식으로 변환하여 반환
    return jsonify([{'menu_id': menu.menu_id, 'name': menu.name, 'price': menu.price, 'image_url': menu.image_url} for menu in menu_data])


# 주문 내역 가져오기
@app.route('/get_orders')
def get_order():
    
    if session['role'] == 'staff':
        order_data = Order.query.all()
        # 메뉴 데이터를 JSON 형식으로 변환하여 반환
        return jsonify([{'id': order.customer_id , 'name': Menu.query.get(order.menu_id).name , 'quantity': order.quantity } for order in order_data])
    else:
        # 메뉴 데이터를 데이터베이스에서 가져오는 코드
        order_data = Order.query.filter_by(customer_id=session.get('user_id')).all()
        # 메뉴 데이터를 JSON 형식으로 변환하여 반환
        return jsonify([{'name': Menu.query.get(order.menu_id).name , 'quantity': order.quantity } for order in order_data])



db.init_app(app)