# run.py
from models import db 
from routes import app

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # SQLAlchemy 모델을 기반으로 데이터베이스 테이블 생성
    app.run(debug=True)