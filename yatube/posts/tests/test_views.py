import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post, User
from posts.views import NUMBER_OF_POSTS

# Общие URLs
INDEX = reverse('posts:index')
POST_CREATE = reverse('posts:post_create')
FOLLOW_INDEX = reverse('posts:follow_index')

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание группы',
        )
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
        posts_list = []
        for i in range(14):
            posts_list.append(
                Post(
                    author=cls.user,
                    text=f'text {i}',
                    group=cls.group,
                )
            )
        # Последний созданный пост с картинкой
        posts_list.append(
            Post(
                author=cls.user,
                text='text 15',
                group=cls.group,
                image=uploaded
            )
        )
        cls.posts_list = Post.objects.bulk_create(posts_list)
        # Экземпляр последнего поста для тестов
        cls.post = Post.objects.latest('pub_date')
        # URLs для тестов с аргументами
        cls.GROUP_LIST = reverse(
            'posts:group_list', kwargs={'slug': cls.post.group.slug})
        cls.PROFILE = reverse(
            'posts:profile', kwargs={'username': cls.post.author})
        cls.POST_DETAIL = reverse(
            'posts:post_detail', kwargs={'post_id': cls.post.id})
        cls.POST_EDIT = reverse(
            'posts:post_edit', kwargs={'post_id': cls.post.id})

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        url_templates_names = (
            (INDEX, 'posts/index.html'),
            (POST_CREATE, 'posts/create_post.html'),
            (self.GROUP_LIST, 'posts/group_list.html'),
            (self.PROFILE, 'posts/profile.html'),
            (self.POST_DETAIL, 'posts/post_detail.html'),
            (self.POST_EDIT, 'posts/create_post.html'),
        )
        for revese_name, template in url_templates_names:
            with self.subTest(revese_name=revese_name):
                response = self.authorized_client.get(revese_name)
                self.assertTemplateUsed(response, template)

    def test_correct_context(self):
        """
        Шаблоны index.html, group_list.html, profile.html.
        Проверка контекста (значений полей первого поста).
        """
        public_urls = (
            INDEX,
            self.GROUP_LIST,
            self.PROFILE,
        )
        for url in public_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                first_object = response.context['page_obj'][0]
                self.assertEqual(first_object.author, self.post.author)
                self.assertEqual(first_object.text, self.post.text)
                self.assertEqual(first_object.group, self.post.group)
                self.assertEqual(first_object.image, self.post.image)

    def test_index_correct_paginator(self):
        """
        Шаблоны index.html, group_list.html, profile.html.
        Проверка паджинатора.
        """
        public_urls = (
            INDEX,
            self.GROUP_LIST,
            self.PROFILE,
        )
        SECOND_PAGE_POSTS_NUMBER = len(self.posts_list) - NUMBER_OF_POSTS
        for url in public_urls:
            with self.subTest(url=url):
                pages = [
                    {
                        'number': 1,
                        'count': NUMBER_OF_POSTS,
                        'url': url,
                    },
                    {
                        'number': 2,
                        'count': SECOND_PAGE_POSTS_NUMBER,
                        'url': url + "?page=2",
                    },
                ]
                for page_info in pages:
                    responce = self.authorized_client.get(page_info['url'])
                    page = responce.context.get('page_obj')
                    self.assertEqual(
                        len(page.object_list), page_info['count'])

    def test_post_detail_correct_context(self):
        """Шаблон post_detail.html. Проверка контекста"""
        response = self.authorized_client.get(self.POST_DETAIL)
        first_object = response.context['post']
        self.assertEqual(first_object.author, self.post.author)
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.group, self.post.group)
        self.assertEqual(first_object.image, self.post.image)
        self.assertIn('form', response.context)

    def test_post_detail_with_comment_correct_context(self):
        """Шаблон post_detail.html.
           После успешной отправки комментарий появляется на странице поста"""
        comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            text='Тестовый комментарий',
        )
        response = self.authorized_client.get(self.POST_DETAIL)
        first_object = response.context['comments'][0]
        self.assertEqual(first_object.author, comment.author)
        self.assertEqual(first_object.text, comment.text)

    def test_post_create_correct_context(self):
        """Шаблон post_create.html, post_edit.html. Проверка контекста"""
        url_names = [
            POST_CREATE,
            self.POST_EDIT
        ]
        for url in url_names:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                form_fields = {
                    'text': forms.fields.CharField,
                    'group': forms.fields.ChoiceField,
                }
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        self.assertIn('form', response.context)
                        form_field = response.context['form'].fields[value]
                        self.assertIsInstance(form_field, expected)

    def test_post_not_in_group(self):
        """Пост не попал в другую группу"""
        URL = self.GROUP_LIST
        post_no_group = Post.objects.create(
            author=self.user,
            text='Post without group',
        )
        pages = [
            {
                'number': 1,
                'url': URL,
            },
            {
                'number': 2,
                'url': URL + "?page=2",
            },
        ]
        for page_info in pages:
            responce = self.authorized_client.get(page_info['url'])
            page = responce.context.get('page_obj')
            self.assertNotIn(post_no_group, page)

    def test_cache_index(self):
        """Проверка кеширования главной страницы.
        """
        post_new = Post.objects.create(
            author=self.user,
            text='Post for cache test',
        )
        response_first = self.guest_client.get(INDEX)
        post_new_text_bytes = bytes(post_new.text, 'UTF-8')
        self.assertIn(post_new_text_bytes, response_first.content)
        post_new.delete()
        response_second = self.guest_client.get(INDEX)
        self.assertEqual(response_first.content, response_second.content)
        cache.clear()
        response_third = self.guest_client.get(INDEX)
        self.assertNotEqual(response_first.content, response_third.content)


class FollowViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='follower')
        cls.another_user = User.objects.create_user(username='another')
        cls.author = User.objects.create_user(username='following')
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст для проверки подписки',
        )
        cls.FOLLOW = reverse(
            'posts:profile_follow', kwargs={'username': cls.author.username})
        cls.UNFOLLOW = reverse(
            'posts:profile_unfollow', kwargs={'username': cls.author.username})

    def setUp(self):
        self.authorized_user = Client()
        self.authorized_another_user = Client()
        self.authorized_user.force_login(self.user)
        self.authorized_another_user.force_login(self.another_user)

    def test_follow_unfollow_work(self):
        """Авторизованный пользователь может подписываться
           на других пользователей и удалять их из подписок.
        """
        follow_count = Follow.objects.count()
        self.authorized_user.get(self.FOLLOW)
        subscrition = Follow.objects.latest('author')
        self.assertTrue(
            Follow.objects.filter(
                id=subscrition.id,
                author=self.author,
            ).exists()
        )
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.authorized_user.get(self.UNFOLLOW)
        self.assertEqual(Follow.objects.count(), follow_count)

    def test_follow_index(self):
        """ Новая запись пользователя появляется
            в ленте тех, кто на него подписан
            и не появляется в ленте тех, кто не подписан.
        """
        Follow.objects.create(user=self.user, author=self.author)
        response = self.authorized_user.get(FOLLOW_INDEX)
        post_text = response.context["page_obj"][0].text
        self.assertEqual(post_text, self.post.text)
        response = self.authorized_another_user.get(FOLLOW_INDEX)
        self.assertNotIn(self.post, response.context["page_obj"])
