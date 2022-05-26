import graphene
from graphene_django import DjangoObjectType, DjangoListField
from graphene_django.filter import DjangoFilterConnectionField
from graphene import relay
from .models import *
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.models import User
from django_filters import FilterSet, OrderingFilter
import django_filters
from .validator import Validator


validator = Validator()


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
   
    author = graphene.Field(AuthorType)
    total_likes =  graphene.Int()
    total_unlikes =  graphene.Int()
   
    def resolve_author(self, info):
        return User.objects.get(id=self.author.id)
    
    def resolve_total_likes(self,info):
        return self.total_likes()

    def resolve_total_unlikes(self,info):
        return self.total_unlikes()

class Query(graphene.ObjectType):
    all_blogs = graphene.List(BlogType)
    blog = graphene.Field(BlogType, blog_id=graphene.Int())

    all_authors = graphene.List(AuthorType)
    author = graphene.Field(AuthorType, author_id=graphene.Int())

    def resolve_all_authors(self, info, **kwargs):
        return User.objects.all()

    def resolve_author(self, info, author_id):
        return User.objects.get(id=author_id)

    def resolve_all_blogs(self, info, **kwargs):
        return Blog.objects.all()

    def resolve_blog(self, info, blog_id):
        return Blog.objects.get(id=blog_id)


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
    img = graphene.String()
    date = graphene.String()
    content = graphene.String()
    author = graphene.Int()

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


class LoginAuthor(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
    token = graphene.String()
    msg = graphene.String()

    @staticmethod
    def mutate(root, info, username, password):
        if not User.objects.filter(username=username).exists():
            return LoginAuthor(token=None, msg="invalid username")
        
        user = authenticate(username=username,password=password)
        if user:
            login(request,user)
            token,_ = Token.objects.get_or_create(request.user)
            return LoginAuthor(token=token.key,msg="Logged in sucessfully!")
        else:
            return LoginAuthor(token=None,msg="Invalid Credentials")

class DeleteAuthor(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
    author = graphene.Field(AuthorType)

    msg = graphene.String()
    @staticmethod
    def mutate(root, info, id):
        if not User.objects.filter(id=id).exists():
            return DeleteAuthor(msg="invalid ID", author=None)

        author_instance = User.objects.get(id=id)
        author_instance.delete()
        return DeleteAuthor(msg="Author Has Been Deleted!",author=None)


class Mutation(graphene.ObjectType):
    create_author = CreateAuthor.Field()
    update_author = UpdateAuthor.Field()
    delete_author = DeleteAuthor.Field()
    login_author = LoginAuthor.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)