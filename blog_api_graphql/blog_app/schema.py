import graphene
from graphene_django import DjangoObjectType, DjangoListField
from graphene_django.filter import DjangoFilterConnectionField
from graphene import relay
from .models import *
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.models import User
from django_filters import FilterSet, OrderingFilter
import django_filters
from .validator import Validator
from datetime import date
import graphql_jwt
from graphql_jwt.shortcuts import get_token


#instance of validator class
validator = Validator()


# Auth Decorator
def authenticate_role(func):
    def wrap(self,info,**kwargs):
        auth_header = info.context.META.get('HTTP_AUTHORIZATION')
        if auth_header is None:
            raise Exception('Authentication Credentials were not provieded!!')
        else:
            new_token=auth_header.replace("JWT","").replace(" ","")
            if UserToken.objects.filter(token=new_token).exists():
                return func(self,info,**kwargs)
            raise Exception("You have logged out!, log in again!")
    return wrap


class TokenType(DjangoObjectType):
    class Meta:
        model=UserToken
        fields=['token','user']

class CommentType(DjangoObjectType):
    class Meta:
        model = Comment
        fields = "__all__"

class BlogListType(DjangoObjectType): 
    class Meta:
        model = Blog
        fields = "__all__"

class AuthorType(DjangoObjectType): 
    class Meta:
        model = User
        fields = "__all__"

    blogs = graphene.List(BlogListType)

    def resolve_blogs(self, info):
        return Blog.objects.filter(author=self.id)

class BlogType(DjangoObjectType): 
    class Meta:
        model = Blog
        fields = "__all__"
   
    comments = graphene.List(CommentType)
    total_comments = graphene.Int()
    total_likes =  graphene.Int()
    total_unlikes =  graphene.Int()
   
    def resolve_comments(self, info):
        return Comment.objects.filter(blog=self.id)
    
    def resolve_total_comments(self, info):
        return Comment.objects.filter(blog=self.id).count()

    def resolve_total_likes(self,info):
        return self.total_likes()

    def resolve_total_unlikes(self,info):
        return self.total_unlikes()

class Query(graphene.ObjectType):
    all_blogs = graphene.List(BlogType)
    blog = graphene.Field(BlogType, blog_id=graphene.ID())

    all_authors = graphene.List(AuthorType)
    author = graphene.Field(AuthorType, author_id=graphene.ID())

    @authenticate_role
    def resolve_all_authors(self, info, **kwargs):
        user = info.context.user
        print(user)
        # if user.is_anonymous:
        #     raise Exception("Authentication credentials were not provided")
        return User.objects.all()

    @authenticate_role
    def resolve_author(self, info, author_id):
        return User.objects.get(id=author_id)

    @authenticate_role
    def resolve_all_blogs(self, info, **kwargs):
        return Blog.objects.all()

    @authenticate_role
    def resolve_blog(self, info, blog_id):
        return Blog.objects.get(id=blog_id)


class storeToken(graphene.Mutation):
    class Arguments:
        username=graphene.String(required=True)
        password=graphene.String(required=True)

    token = graphene.Field(TokenType)
    msg=graphene.String()

    def mutate(self,info,username,password):
        token=None
        if not User.objects.filter(username=username).exists():
            return storeToken(token=None, msg="invalid username !")
        valid_user = authenticate(username=username,password=password)
        if valid_user:
            user_obj = User.objects.get(username=username)
            if User.objects.filter(id=user_obj.id).exists():
                if UserToken.objects.filter(user_id=user_obj.id).exists():
                    token_obj=UserToken.objects.get(user_id=user_obj.id)
                    print(token_obj,"@@@@@@@@@@@@@@@@@@@@@@@@")
                    return storeToken(token=token_obj, msg="logged in Successfully!")
                else:
                    user = User.objects.get(id=user_obj.id)
                    token = get_token(user)
                    token_obj=UserToken(token=token,user=User.objects.get(id=user_obj.id))
                    token_obj.save()
                    return storeToken(token=token_obj, msg="logged in Successfully!")
            else:
                return storeToken(token=None,msg="Invalid username!")
        else:
            return storeToken(token=None,msg="Invalid Credentials!")


class AuthorInput(graphene.InputObjectType):
    id = graphene.ID()
    username = graphene.String()
    first_name = graphene.String()
    last_name = graphene.String()
    email = graphene.String()
    password = graphene.String()

class BlogInput(graphene.InputObjectType):
    id = graphene.ID()
    title = graphene.String()
    date = graphene.String()
    img_link = graphene.String()
    content = graphene.String()
    author = graphene.ID()

class CommentInput(graphene.InputObjectType):
    id = graphene.ID()
    comment = graphene.String()
    blog = graphene.ID()
    commentor = graphene.ID() 

class CreateAuthor(graphene.Mutation):
    class Arguments:
        author_data = AuthorInput(required=True)
    author = graphene.Field(AuthorType)
    msg = graphene.String()

    @staticmethod
    def mutate(root, info, author_data=None):
        # username validator
        if author_data.username is not None:
            response = validator.validate_username(author_data.username)
            if not response['is_valid']:
                return CreateAuthor(msg=response['msg'],author=None)
        else:
            return CreateAuthor(msg="username required",author=None)

        #name validator
        if author_data.first_name is not None and author_data.last_name is not None:
            response = validator.validate_name(author_data.first_name,author_data.last_name)
            if not response['is_valid']:
                return CreateAuthor(msg=response['msg'],author=None)
            else:
                if author_data.first_name is None:
                    return CreateAuthor(msg="first_name required",author=None)
                if author_data.last_name is None:
                    return CreateAuthor(msg="last_name required",author=None)

        #email validator
        if author_data.email is not None:
            response = validator.validate_email(author_data.email)
            if not response['is_valid']:
                return CreateAuthor(msg=response['msg'],author=None)
        else:
            return CreateAuthor(msg="email required",author=None)

        #pasword validator
        if author_data.password is not None:
            response = validator.validate_password(author_data.password)
            if not response['is_valid']:
                return CreateAuthor(msg=response['msg'],author=None)
        else:
            return CreateAuthor(msg="password required",author=None)

        author_instance = User( 
            first_name=author_data.first_name,
            last_name=author_data.last_name,
            username=author_data.username,
            email=author_data.email
        )
        author_instance.set_password(author_data.password)
        author_instance.save()
        return CreateAuthor(msg="Author has been created!",author=author_instance)


class UpdateAuthor(graphene.Mutation):
    class Arguments:
        author_data = AuthorInput(required=True)
    author = graphene.Field(AuthorType)
    msg = graphene.String()

    @staticmethod
    @authenticate_role
    def mutate(root, info, author_data=None):

        if author_data.id is not None:
            if not User.objects.filter(id=int(author_data.id)).exists():
                return UpdateAuthor(msg="No Account Associated with given ID",author=None)
        else:
            return UpdateAuthor(msg="ID required",author=None)

        # username validator
        if author_data.username is not None:
            response = validator.validate_username(author_data.username,author_data.id)
            if not response['is_valid']:
                return UpdateAuthor(msg=response['msg'],author=None)
        
        #name validator
        if author_data.first_name is not None and author_data.last_name is not None:
            response = validator.validate_name(author_data.first_name,author_data.last_name)
            if not response['is_valid']:
                return UpdateAuthor(msg=response['msg'],author=None)

        #email validator
        if author_data.email is not None:
            response = validator.validate_email(author_data.email)
            if not response['is_valid']:
                return UpdateAuthor(msg=response['msg'],author=None)
        else:
            return UpdateAuthor(msg="email required",author=None)

        author_instance = User.objects.get(id=int(author_data.id))
        
        if author_data.first_name is not None:
            author_instance.first_name=author_data.first_name

        if author_data.last_name is not None:
            author_instance.last_name=author_data.last_name

        if author_data.username is not None:
            author_instance.username=author_data.username

        if author_data.email is not None:
            author_instance.email=author_data.email

        author_instance.save()
        return UpdateAuthor(msg="Author has been Updated!",author=author_instance)


class LogoutAuthor(graphene.Mutation):
    class Arguments:
        author_id = graphene.ID(required=True)

    msg = graphene.String()

    @staticmethod
    def mutate(root,info,author_id):
        if UserToken.objects.filter(user_id=author_id).exists():
            obj=UserToken.objects.get(user_id=author_id)
            obj.delete()
            return LogoutAuthor(msg='succfully logout!')
        else:
            return LogoutAuthor(msg='succfully logout!')



class DeleteAuthor(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
    author = graphene.Field(AuthorType)

    msg = graphene.String()
    @staticmethod
    @authenticate_role
    def mutate(root, info, id):
        if not User.objects.filter(id=id).exists():
            return DeleteAuthor(msg="invalid ID", author=None)

        author_instance = User.objects.get(id=id)
        author_instance.delete()
        return DeleteAuthor(msg="Author Has Been Deleted!",author=None)


class CreateBlog(graphene.Mutation):
    class Arguments:
        blog_data = BlogInput(required=True)
    blog = graphene.Field(BlogType)
    msg = graphene.String()

    @staticmethod
    @authenticate_role
    def mutate(root, info, blog_data=None):
        if blog_data.title is not None:
            if len(blog_data.title.strip()) == 0:
                return CreateBlog(msg="title must not be blank",blog=None)
        else:
            return CreateBlog(msg="title required!",blog=None)

        if blog_data.content is not None:
            if len(blog_data.content.strip()) == 0:
                return CreateBlog(msg="content must not be blank",blog=None)
        else:
            return CreateBlog(msg="content required!",blog=None)
        
        if blog_data.author is not None:
            if not User.objects.filter(id=blog_data.author).exists():
                return CreateBlog(msg="invalid blog ID ",blog=None)
        else:
            return CreateBlog(msg="author required")

        today = date.today()
        today_date = today.strftime("%B %d, %Y")
        blog_instance = Blog( 
            title=blog_data.title,
            date=today_date,
            content=blog_data.content,
            author=User.objects.get(id=blog_data.author),
            img_link = blog_data.img_link
        )
        blog_instance.save()
        return CreateBlog(msg="Blog has been created!",blog=blog_instance)

class UpdateBlog(graphene.Mutation):
    class Arguments:
        blog_data = BlogInput(required=True)
    blog = graphene.Field(BlogType)
    msg = graphene.String()

    @staticmethod
    @authenticate_role
    def mutate(root, info, blog_data=None):
        if blog_data.id is not None:
            if not Blog.objects.filter(id=blog_data.id).exists():
                return UpdateBlog(msg="invalid blog ID",blog=None)
        else:
            return UpdateBlog(msg="blog ID required!",blog=None)

        if blog_data.title is not None:
            if len(blog_data.title.strip()) == 0:
                return UpdateBlog(msg="title must not be blank",blog=None)

        if blog_data.content is not None:
            if len(blog_data.content.strip()) == 0:
                return UpdateBlog(msg="content must not be blank",blog=None)

        blog_instance = Blog.objects.get(id=blog_data.id)

        if blog_data.img_link is not None:
            blog_instance.img_link=blog_data.img_link
        if blog_data.title is not None:
            blog_instance.title=blog_data.title
        if blog_data.content is not None:
            blog_instance.content=blog_data.content
        blog_instance.save()

        return UpdateBlog(msg="Blog has been Updated!",blog=blog_instance)


class DeleteBlog(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
    blog = graphene.Field(BlogType)
    msg = graphene.String()

    @staticmethod
    @authenticate_role
    def mutate(root, info, id):
        if not Blog.objects.filter(id=id).exists():
            return DeleteBlog(msg="invalid ID", blog=None)
        blog_instance = Blog.objects.get(id=id)
        blog_instance.delete()
        return DeleteBlog(msg="Blog Has Been Deleted!",blog=None)


class LikeBlog(graphene.Mutation):
    class Arguments:
        blog_id = graphene.ID(required=True)
        author_id = graphene.ID(required=True)
    msg = graphene.String()

    @staticmethod
    @authenticate_role
    def mutate(root, info, blog_id, author_id):
        if blog_id is not None:
            if not Blog.objects.filter(id=blog_id).exists():
                return LikeBlog(msg="invalid blog ID")
        else:
            return LikeBlog(msg="blog_id required!")

        if author_id is not None:
            if not User.objects.filter(id=author_id).exists():
                return LikeBlog(msg="invalid Author ID")
        else:
            return LikeBlog(msg="author_id required!")

        blog = Blog.objects.get(id=blog_id)
        user = User.objects.get(id=author_id)

        if blog.likes.filter(id=user.id).exists():
            blog.likes.remove(user)
            return LikeBlog(msg="Remove Like Successfully!")
        else:
            blog.likes.add(user)
            if blog.unlikes.filter(id=user.id).exists():
                blog.unlikes.remove(user)
            return LikeBlog(msg="Job has been Liked Successfully!")


class UnikeBlog(graphene.Mutation):
    class Arguments:
        blog_id = graphene.ID(required=True)
        author_id = graphene.ID(required=True)
    msg = graphene.String()

    @staticmethod
    @authenticate_role
    def mutate(root, info, blog_id, author_id):
        if blog_id is not None:
            if not Blog.objects.filter(id=blog_id).exists():
                return LikeBlog(msg="invalid blog ID")
        else:
            return LikeBlog(msg="blog_id required!")

        if author_id is not None:
            if not User.objects.filter(id=author_id).exists():
                return LikeBlog(msg="invalid Author ID")
        else:
            return LikeBlog(msg="author_id required!")

        blog = Blog.objects.get(id=blog_id)
        user = User.objects.get(id=author_id)
        
        if blog.unlikes.filter(id=user.id).exists():
            blog.unlikes.remove(user)
            return UnikeBlog(msg="Remove Unike Successfully!")
        else:
            blog.unlikes.add(user)
            if blog.likes.filter(id=user.id).exists():
                blog.likes.remove(user)
            return UnikeBlog(msg="Job has been Uniked Successfully!")

class CreateComment(graphene.Mutation):
    class Arguments:
        comment_data = CommentInput(required=True)
    comment = graphene.Field(CommentType)
    msg = graphene.String()

    @staticmethod
    @authenticate_role
    def mutate(root, info, comment_data=None):

        if comment_data.comment is not None:
            if len(comment_data.comment.strip()) == 0:
                return CreateComment(msg="comment must not be blank",comment=None)
        else:
            return CreateComment(msg="comment required!",comment=None)
        
        if comment_data.blog is not None:
            if not Blog.objects.filter(id=comment_data.blog).exists():
                return CreateComment(msg="invalid blog ID",comment=None)
        else:
            return CreateComment(msg="blog required!",comment=None)

        if comment_data.commentor is not None:
            if not User.objects.filter(id=comment_data.commentor).exists():
                return CreateComment(msg="invalid commentor ID ",comment=None)
        else:
            return CreateComment(msg="commentor required",comment=None)

        if Blog.objects.get(id=comment_data.blog).author == User.objects.get(id=comment_data.commentor).id:
            return CreateComment(msg="Author cannot comment on own blog!",comment=None)
        
        comment_instance = Comment( 
            comment=comment_data.comment,
            blog=Blog.objects.get(id=comment_data.blog),
            commentor=User.objects.get(id=comment_data.commentor),
        )
        comment_instance.save()
        return CreateComment(msg="comment has been created!",comment=comment_instance)


class UpdateComment(graphene.Mutation):
    class Arguments:
        comment_data = CommentInput(required=True)
    comment = graphene.Field(CommentType)
    msg = graphene.String()

    @staticmethod
    @authenticate_role
    def mutate(root, info, comment_data=None):

        if comment_data.id is not None:
            if not Comment.objects.filter(id=comment_data.id).exists():
                return CreateComment(msg="invalid Comment ID",comment=None)
        else:
            return CreateComment(msg="ID required", comment=None)

        if comment_data.comment is not None:
            if len(comment_data.comment.strip()) == 0:
                return CreateComment(msg="comment must not be blank",comment=None)

        comment_instance = Comment.objects.get(id=comment_data.id)
        if comment_data.comment is not None:
            comment_instance.comment=comment_data.comment
        comment_instance.save()

        return CreateComment(msg="comment has been Updated!",comment=comment_instance)


class DeleteComment(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
    comment = graphene.Field(CommentType)
    msg = graphene.String()

    @staticmethod
    @authenticate_role
    def mutate(root, info, id):
        if not Comment.objects.filter(id=id).exists():
            return DeleteComment(msg="invalid ID", comment=None)
        comment_instance = Comment.objects.get(id=id)
        comment_instance.delete()
        return DeleteComment(msg="Comment Has Been Deleted!",comment=None)


class Mutation(graphene.ObjectType):
    create_author = CreateAuthor.Field()
    update_author = UpdateAuthor.Field()
    delete_author = DeleteAuthor.Field()
    logout_author = LogoutAuthor.Field()
    create_blog = CreateBlog.Field()
    update_blog = UpdateBlog.Field()
    delete_blog = DeleteBlog.Field()
    like_blog = LikeBlog.Field()
    unlike_blog = UnikeBlog.Field()
    create_comment = CreateComment.Field()
    update_comment = UpdateComment.Field()
    delete_comment = DeleteComment.Field()
    # token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    # verify_token = graphql_jwt.Verify.Field()
    # refresh_token = graphql_jwt.Refresh.Field()
    login_author = storeToken.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)