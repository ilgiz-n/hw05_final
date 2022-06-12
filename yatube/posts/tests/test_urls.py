from http import HTTPStatus
from urllib.parse import urljoin

from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User

# URLs
INDEX = reverse('posts:index')
POST_CREATE = reverse('posts:post_create')
LOGIN_URL = reverse('users:login')
UNEXISTING_PAGE = '/unexisting_page/'


class PostURLTests(TestCase):
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
            text='Т' * 100,
            group=cls.group,
        )
        # URLs для тестов с аргументами
        cls.GROUP_LIST = reverse(
            'posts:group_list', kwargs={'slug': cls.post.group.slug})
        cls.PROFILE = reverse(
            'posts:profile', kwargs={'username': cls.post.author})
        cls.POST_DETAIL = reverse(
            'posts:post_detail', kwargs={'post_id': cls.post.id})
        cls.POST_EDIT = reverse(
            'posts:post_edit', kwargs={'post_id': cls.post.id})

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_public_pages(self):
        """Проверка общедоступных страниц"""
        public_urls = (
            INDEX,
            self.GROUP_LIST,
            self.PROFILE,
            self.POST_DETAIL
        )
        for url in public_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        url_templates_names = (
            (INDEX, 'posts/index.html'),
            (POST_CREATE, 'posts/create_post.html'),
            (self.GROUP_LIST, 'posts/group_list.html'),
            (self.PROFILE, 'posts/profile.html'),
            (self.POST_DETAIL, 'posts/post_detail.html'),
            (self.POST_EDIT, 'posts/create_post.html'),
            (UNEXISTING_PAGE, 'core/404.html'),
        )
        for url, template in url_templates_names:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_create_url_exists_for_author(self):
        """Доступ автора к странице создания и редактирования постов.
        """
        post_urls = (
            self.POST_EDIT,
            POST_CREATE
        )
        for url in post_urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_id_url_not_exists_for_guest(self):
        """Переадресация неавторизованному пользователю
           со страниц создания и редактирования постов
           на страницу авторизации.
        """
        post_urls = (
            self.POST_EDIT,
            POST_CREATE
        )
        for url in post_urls:
            REDIRECT_LOGIN_URL = urljoin(LOGIN_URL, f'?next={url}')
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(
                    response, REDIRECT_LOGIN_URL)

    def test_post_edit_url_exists_for_author_only(self):
        """Переадресация к деталям поста,
           при попытке редактирования неавтором.
        """
        POST_EDIT = 'posts:post_edit'
        POST_DETAIL = 'posts:post_detail'
        self.user_Leo = User.objects.create_user(username='leo')
        self.post_Leo = Post.objects.create(
            author=self.user_Leo,
            text='leo text',
        )
        response = self.authorized_client.get(
            reverse(POST_EDIT, kwargs={'post_id': self.post_Leo.id}))
        self.assertRedirects(
            response, reverse(
                POST_DETAIL, kwargs={'post_id': self.post_Leo.id}))

    def test_unexisting_page(self):
        """HTTPStatus.NOT_FOUND в запросе на несуществующую странцу.
        """
        response = self.guest_client.get(UNEXISTING_PAGE)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_comment_allowed_for_authorized_only(self):
        """Переадресация на страницу входа для неавтаризованного пользователя
           со страницы добавления комментария. (Комментировать посты может
           только авторизованный пользователь).
        """
        COMMENT_URL = reverse(
            'posts:add_comment', kwargs={'post_id': self.post.id})
        REDIRECT_LOGIN_URL = urljoin(LOGIN_URL, f'?next={COMMENT_URL}')
        response = self.guest_client.get(COMMENT_URL)
        self.assertRedirects(response, REDIRECT_LOGIN_URL)
