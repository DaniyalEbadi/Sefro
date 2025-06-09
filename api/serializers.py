from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import Role, Permission, RolePermission, UserRole, Category, Article, Comment, Media, ArticleLike, ArticleView

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    username = serializers.CharField(required=False)  # Make username optional as we'll generate it if not provided
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'first_name', 'last_name', 'is_email_verified')
        extra_kwargs = {
            'id': {'read_only': True},
            'is_email_verified': {'read_only': True},
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def create(self, validated_data):
        # Check if username was provided, otherwise generate it from email
        if not validated_data.get('username'):
            email = validated_data.get('email')
            username = email.split('@')[0]  # Use part before @ as base username
            
            # If username already exists, append numbers until we find a unique one
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
                
            # Add username to validated data
            validated_data['username'] = username
        
        # Create user with encrypted password
        user = User.objects.create_user(**validated_data)
        return user

    def update(self, instance, validated_data):
        # Handle password update separately
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)
        
        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = '__all__'

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'

class RolePermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RolePermission
        fields = '__all__'

class UserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRole
        fields = '__all__'

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = '__all__'

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'

class ArticleLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleLike
        fields = '__all__'

class ArticleViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleView
        fields = '__all__'

class ArticleSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    # Category will be writable by ID, and represented nestedly by category_details
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    category_details = CategorySerializer(source='category', read_only=True)
    media_files = MediaSerializer(many=True, read_only=True, source='media') # Corrected source
    comments = CommentSerializer(many=True, read_only=True)
    likes_count = serializers.SerializerMethodField()
    views_count = serializers.SerializerMethodField()

    class Meta:
        model = Article
        # Ensure all desired fields are listed, especially if adding new ones like category_id implicitly
        # fields = '__all__' might not behave as expected with explicit field definitions conflicting with model fields.
        # All fields to be included in the serializer must be listed here if Meta.fields is a tuple.
        fields = (
            'id', 'author', 'category', 'category_details', 'title', 'slug', 'content',
            'seo_title', 'seo_description', 'Main_image', 'status',
            'media_files', 'comments', 'likes_count', 'views_count',
            'view_count', 'created_at', 'updated_at', 'published_at'
        )
        read_only_fields = (
            'slug', 'view_count', 'created_at', 'updated_at', 'published_at',
            'author', 'category_details', 'media_files', 'comments'
        )
        # 'category' is now writable (accepts ID)

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_views_count(self, obj):
        return obj.views.count()

    def create(self, validated_data):
        # Author is set from context (already handled by the serializer if request is in context)
        # Category is set via category_id field thanks to source='category'
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)
