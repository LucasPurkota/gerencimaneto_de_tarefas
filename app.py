from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from models import db, User, Task

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tarefas.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Nome de usuário já existe.')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email já cadastrado.')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Conta criada com sucesso! Faça login.')
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
            flash('Login realizado com sucesso!')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuário ou senha incorretos.')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Você foi desconectado.')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user_tasks = Task.query.filter((Task.author_id == user_id) | (Task.assignee_id == user_id)).all()
    
    pending = Task.query.filter(
        ((Task.author_id == user_id) | (Task.assignee_id == user_id)) & 
        (Task.status == 'pendente')
    ).count()
    
    in_progress = Task.query.filter(
        ((Task.author_id == user_id) | (Task.assignee_id == user_id)) & 
        (Task.status == 'em_andamento')
    ).count()
    
    completed = Task.query.filter(
        ((Task.author_id == user_id) | (Task.assignee_id == user_id)) & 
        (Task.status == 'concluida')
    ).count()
    
    return render_template('dashboard.html', 
                          tasks=user_tasks, 
                          pending=pending, 
                          in_progress=in_progress, 
                          completed=completed)

@app.route('/tasks')
def tasks():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    status_filter = request.args.get('status', 'all')
    
    query = Task.query.filter((Task.author_id == user_id) | (Task.assignee_id == user_id))
    
    if status_filter != 'all':
        query = query.filter(Task.status == status_filter)
    
    user_tasks = query.order_by(Task.created_at.desc()).all()
    users = User.query.all()
    
    return render_template('tasks.html', tasks=user_tasks, users=users, status_filter=status_filter)

@app.route('/create_task', methods=['GET', 'POST'])
def create_task():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        status = request.form['status']
        assignee_id = request.form['assignee']
        due_date_str = request.form['due_date']
        
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d') if due_date_str else None
        
        task = Task(
            title=title,
            description=description,
            status=status,
            author_id=session['user_id'],
            assignee_id=assignee_id,
            due_date=due_date
        )
        
        db.session.add(task)
        db.session.commit()
        
        flash('Tarefa criada com sucesso!')
        return redirect(url_for('tasks'))
    
    users = User.query.all()
    return render_template('create_task.html', users=users)

@app.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    task = Task.query.get_or_404(task_id)
    
    if task.author_id != session['user_id'] and task.assignee_id != session['user_id']:
        flash('Você não tem permissão para editar esta tarefa.')
        return redirect(url_for('tasks'))
    
    if request.method == 'POST':
        task.title = request.form['title']
        task.description = request.form['description']
        task.status = request.form['status']
        task.assignee_id = request.form['assignee']
        due_date_str = request.form['due_date']
        
        task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d') if due_date_str else None
        
        db.session.commit()
        flash('Tarefa atualizada com sucesso!')
        return redirect(url_for('tasks'))
    
    users = User.query.all()
    return render_template('edit_task.html', task=task, users=users)

@app.route('/delete_task/<int:task_id>')
def delete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    task = Task.query.get_or_404(task_id)
    
    if task.author_id != session['user_id'] and task.assignee_id != session['user_id']:
        flash('Você não tem permissão para excluir esta tarefa.')
        return redirect(url_for('tasks'))
    
    db.session.delete(task)
    db.session.commit()
    flash('Tarefa excluída com sucesso!')
    return redirect(url_for('tasks'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)