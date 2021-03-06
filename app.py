from flask import Flask, render_template, redirect, request, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

from data import db_session
from data.users import User
from flask_socketio import SocketIO

from data.user_forms import LoginForm, RegisterForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'switterry_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
socketio = SocketIO(app)


class Articles(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    intro = db.Column(db.String(250), nullable=False)
    text = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow())

    def __repr__(self):
        return '<Article %r>' % self.id


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


# Страница с добавлением постов
@app.route('/create_post', methods=['POST', 'GET'])
def create_post():
    if request.method == "POST":
        title = request.form['title']
        intro = request.form['intro']
        text = request.form['text']
        article = Articles(title=title, intro=intro, text=text)

        try:
            db.session.add(article)
            db.session.commit()
            return redirect('/news_feed')
        except:
            return "При добавлении поста произошла ошибка"
    else:
        return render_template("create_post.html")


# Cтраница с лентой
@app.route('/news_feed')
def main_page():
    articles = Articles.query.order_by(Articles.date.desc()).all()
    return render_template("news_feed.html", articles=articles)


@app.route('/registration', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
    return render_template('register.html', tittle='Registration', form=form)


@app.route("/")
def index():
    if not current_user.is_authenticated:
        return redirect("/auth")

    else:
        return redirect(f"/prof{current_user.id}")


@app.route("/prof<prof_id>")
def profile(prof_id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == prof_id).first()
    return render_template("prof_page_base.html", name=user.name)


@app.route('/auth', methods=['GET', 'POST'])
def login():
    db_sess = db_session.create_session()
    login_form = LoginForm()
    register_form = RegisterForm()

    if register_form.validate_on_submit():
        if register_form.password.data == register_form.password_again.data:
            new_user = User(name=register_form.name.data,
                            email=register_form.email.data)
            new_user.set_password(register_form.password.data)

            db_sess.add(new_user)
            db_sess.commit()
            db_sess.refresh(new_user)

            login_user(new_user, remember=register_form.remember_me.data)

        return redirect("/")

    if login_form.validate_on_submit():
        user = db_sess.query(User).filter(User.email == login_form.email.data).first()
        if user and user.check_password(login_form.password.data):
            login_user(user, remember=login_form.remember_me.data)
            # print(user.id)
            return redirect("/")

    return render_template('auth.html', title='Authorization', login_form=login_form, reg_form=register_form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/news_feed')
def main():
    db_session.global_init("db/users.sqlite")
    app.run()


if __name__ == '__main__':
    main()
