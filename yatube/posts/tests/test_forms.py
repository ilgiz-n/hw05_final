import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Group, Post, User

POST_CREATE = reverse('posts:post_create')

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание группы',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_create(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            POST_CREATE,
            data=form_data,
            follow=True,
        )
        post = Post.objects.latest('pub_date')
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.image.name, 'posts/small.gif')
        PROFILE_URL = reverse(
            'posts:profile', kwargs={'username': post.author})
        self.assertRedirects(response, PROFILE_URL)

    def test_post_edit(self):
        """Редактирование записи в Post."""
        post = Post.objects.create(
            author=self.user,
            text='Тестовый текст',
            group=self.group,
        )
        posts_count = Post.objects.count()
        second_group = Group.objects.create(
            title='Вторая группа',
            slug='second_group_slug',
            description='Тестовое описание второй группы',
        )
        edited_form_data = {
            'text': 'Измененный текст',
            'group': second_group.id,
        }
        response_edited = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.id}),
            data=edited_form_data,
            follow=True,
        )
        post = Post.objects.get(id=post.id)
        self.assertEqual(response_edited.status_code, HTTPStatus.OK)
        self.assertEqual(post.text, edited_form_data['text'])
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group.id, edited_form_data['group'])
        self.assertEqual(Post.objects.count(), posts_count)
        POST_DETAIL_URL = reverse(
            'posts:post_detail', kwargs={'post_id': post.id})
        self.assertRedirects(response_edited, POST_DETAIL_URL)

    def test_comment_create(self):
        """Валидная форма создает комментарий"""
        COMMENT_URL = reverse(
            'posts:add_comment', kwargs={'post_id': self.post.id})
        POST_DETAIL_URL = reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id})
        comments_count = Comment.objects.count()
        form_data = {
            'post': self.post.id,
            'author': self.user,
            'text': 'Тестовый комментарий',
        }
        response = self.authorized_client.post(
            COMMENT_URL,
            data=form_data,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        comment = Comment.objects.latest('created')
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.author, form_data['author'])
        self.assertEqual(comment.post.id, form_data['post'])
        self.assertRedirects(response, POST_DETAIL_URL)
