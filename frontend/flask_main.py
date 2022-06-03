import requests
from werkzeug.utils import secure_filename
import os
from flask import Flask,render_template,redirect,request,session, url_for,flash
from graphqlclient import GraphQLClient

app = Flask(__name__)
app.secret_key = "56ce867a3a3a23a3a2"

url="http://127.0.0.1:8000/graphql"

UPLOAD_FOLDER = 'static/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

token=None

@app.route("/",methods=['POST','GET'])
def login():
    if 'username' not in session:

        if request.method=='POST':
            username=request.form['username']
            password=request.form['password']
            query ='''mutation
                            {
                                loginAuthor(username:"%s",password:"%s")
                                {
                                    token{
                                            token
                                            user{
                                                id,
                                                username
                                            }
                                        }
                                msg
                                }
                            }''' % (username,password)       
          
            r=requests.post(url=url,json={"query":query})
            if r.json()['data']['loginAuthor']['token'] is None:
                msg=r.json()['data']['loginAuthor']['msg']
                flash(msg)
                return render_template("login.html")
            else:
                session['token']=r.json()['data']['loginAuthor']['token']['token']
                session['user_id']=r.json()['data']['loginAuthor']['token']['user']['id']
                session['username']=r.json()['data']['loginAuthor']['token']['user']['username']
                return redirect(url_for('dashboard'))
        return render_template("login.html")
    else:
        return redirect(url_for('dashboard'))


@app.route("/register/", methods=['POST', 'GET'])
def register():
    if request.method=='POST':
        first_name=request.form['fname']
        last_name=request.form['lname']
        username=request.form['username']
        email=request.form['email']
        password=request.form['password']
        query ='''mutation{
                        createAuthor(authorData: {username: "%s", firstName: "%s", lastName: "%s", email: "%s", password: "%s"}){
                                author{
                                        id,
                                        username,
                                        email,
                                        firstName,
                                        lastName,
                                    }
                                msg
                            }
                        }''' % (username, first_name, last_name, email, password)
        response=requests.post(url=url,json={"query":query})
        data=response.json()
        print(response.json())
        if response.json()['data']['createAuthor']['author'] is None:
            msg=response.json()['data']['createAuthor']['msg']
            flash(msg)
            return redirect(url_for('register'))
        else:
            msg=response.json()['data']['createAuthor']['msg']
            flash(msg)
            return redirect(url_for('login'))
    return render_template('register.html')


@app.route("/dashboard/", methods=['POST', 'GET'])
def dashboard():
    if 'username' in session:
        query='''query{
                allBlogs{
                        id,
                        title,
                        imgLink,
                        content,
                        totalLikes,
                        totalUnlikes,
                        totalComments
                        date
                        author
                            {   
                                id
                                username
                            }
                        }
                    }'''
        headers = {'Authorization': f"JWT {session['token']}"}
        response=requests.post(url=url,json={"query":query},headers=headers)
        print(response.json())
        if response.json()['data']['allBlogs'] is None:
            data=response.json()
            msg=data["errors"][0]["message"]
            flash(msg)
            return render_template('login.html')
        else:
            blogs=response.json()['data']['allBlogs']
            return render_template('author_index.html',blogs=blogs)
    else:
        return redirect(url_for('login'))


@app.route('/logout/',methods=['GET', 'POST'])
def logout():
    id=session['user_id']
    query='''mutation{
                    logoutAuthor(authorId:%s)
                        {
                            msg
                        }  
                    }'''% (id)

    response=requests.post(url=url,json={"query":query})
    session.pop('username', None)                
    session.pop('user_id', None)
    session.pop('token', None)
    # session.pop('liked', None)
    msg=response.json()['data']['logoutAuthor']['msg']
    flash(msg)
    return redirect(url_for('login'))


@app.route('/edit/<id>',methods=['GET', 'POST'])
def edit(id):
    query = ''' query blog {
                        blog(blogId: %s) {
                        title
                        imgLink
                        content
                        }
                        }'''% (id)
    headers = {'Authorization': f"JWT {session['token']}"}
    response=requests.post(url=url,json={"query":query},headers=headers)
    
    if request.method == "POST":
        title=request.form['title']
        content=request.form['body']
        file = request.files['image']
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        image=file.filename
        query='''mutation updateMutation
                {
                updateBlog(blogData:{
                    id:%s,
                    title:"%s",
                    content:"%s",
                    imgLink:"%s",
                    })
                    {
                        msg
                }
                }''' % (id,title,content,image)
        response=requests.post(url=url,json={"query":query},headers=headers)
        flash(response.json()['data']['updateBlog']['msg'])
        return redirect(url_for('dashboard'))
    return render_template('edit_post.html',blog=response.json()['data'])




@app.route('/delete/<int:id>',methods=['GET','POST'])
def delete(id):
    if 'username' in session:
        query='''mutation deleteMutation
                    {
                    deleteBlog(id:%s) 
                        {
                            msg
                        }
                    }'''% (id)
        headers = {'Authorization': f"JWT {session['token']}"}
        response=requests.post(url=url,json={"query":query},headers=headers)
        print(response.json()['data'])
        flash(response.json()['data']['deleteBlog']['msg'])
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))



@app.route('/post/',methods=['GET','POST'])
def post():
    if 'username' in session:
        if request.method == "POST":
            title=request.form['title']
            content=request.form['body']
            file = request.files['image']
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image=file.filename
            query='''mutation createMutation
                    {
                    createBlog(blogData:{
                        title:"%s",
                        content:"%s",
                        imgLink:"%s",
                        author:"%s"
                        })
                        {
                            msg
                    }
                    }''' % (title,content,image,session['user_id'])

            headers = {'Authorization': f"JWT {session['token']}"}
            response=requests.post(url=url,json={"query":query},headers=headers)
            flash(response.json()['data']['createBlog']['msg'])
            return redirect(url_for('dashboard'))
        return render_template('blog_post.html')
    else:
        return redirect(url_for('login'))


@app.route('/blog/<id>',methods=['GET','POST'])
def blog(id):
    if 'username' in session:
        query='''query singleBlog{
                blog(blogId:"%s"){
                        id,
                        title,
                        imgLink,
                        content,
                        totalLikes,
                        totalUnlikes,
                        totalComments
                        likes{
                        username
                        }
                        unlikes{
                        username
                        }
                        date
                        comments{
                        comment
                        commentor{
                        username
                        }
                        }
                        author
                            {   
                                id
                                username
                            }
                        }
                    }''' % (id)
        headers = {'Authorization': f"JWT {session['token']}"}
        response=requests.post(url=url,json={"query":query},headers=headers)
        liked = False
        unliked = False
        if response.json()['data']['blog'] is None:
            data=response.json()
            msg=data["errors"][0]["message"]
            flash(msg)
            return redirect(url_for('dashboard'))
        else:
            blog=response.json()['data']['blog']
            for i in blog['likes']:
                if i['username'] == session['username']:
                    liked = True
                    break
            for i in blog['unlikes']:
                if i['username'] == session['username']:
                    unliked = True
                    break
            return render_template('view_post.html',blog=blog, liked=liked,unliked=unliked)
    else:
        return redirect(url_for('login'))

@app.route('/blog_like/<id>',methods=['GET','POST'])
def blog_like(id):
    if 'username' in session:
        query='''mutation likeBlogMutation {
                        likeBlog(authorId: "%s", blogId: "%s") {
                        msg
                        }
                        }''' % (session['user_id'],id)
        headers = {'Authorization': f"JWT {session['token']}"}
        response=requests.post(url=url,json={"query":query},headers=headers)
        if response.json()['data']['likeBlog'] is None:
            data=response.json()
            msg=data["errors"][0]["message"]
            flash(msg)
            return redirect(f"/blog/{id}")
        else:
            return redirect(f"/blog/{id}")
    else:
        return redirect(url_for('login'))

@app.route('/blog_unlike/<id>',methods=['GET','POST'])
def blog_unlike(id):
    if 'username' in session:
        query='''mutation unlikeBlogMutation {
                        unlikeBlog(authorId: "%s", blogId: "%s") {
                        msg
                        }
                        }''' % (session['user_id'],id)
        headers = {'Authorization': f"JWT {session['token']}"}
        response=requests.post(url=url,json={"query":query},headers=headers)
        if response.json()['data']['unlikeBlog'] is None:
            data=response.json()
            msg=data["errors"][0]["message"]
            flash(msg)
            return redirect(f"/blog/{id}")
        else:
            return redirect(f"/blog/{id}")
    else:
        return redirect(url_for('login'))

@app.route('/comment/',methods=['GET','POST'])
def comment():
    if 'username' in session:
        comment = request.form['comment']
        id = request.form['blog_id']
        query='''mutation createCommentMutation {
                            createComment(
                            commentData: {
                            comment: "%s", 
                            blog: "%s", 
                            commentor: "%s"}) {
                            comment {
                            id
                            comment
                            commentor {
                                firstName
                                lastName
                                }
                            }
                            msg
                            }
                            }''' % (comment,id,session['user_id'])
        headers = {'Authorization': f"JWT {session['token']}"}
        response=requests.post(url=url,json={"query":query},headers=headers)
        if response.json()['data']['createComment'] is None:
            data=response.json()
            msg=data["errors"][0]["message"]
            flash(msg)
            return redirect(f"/blog/{id}")
        else:
            return redirect(f"/blog/{id}")
    else:
        return redirect(url_for('login'))
if __name__ == "__main__":
    app.run(debug=True, port=5000)