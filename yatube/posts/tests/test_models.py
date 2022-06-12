from django.db.utils import IntegrityError
from django.test import TestCase

from posts.models import POST_OBJECT_NAME_LENGHT, Follow, Group, Post, User


class PostModelTest(TestCase):
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
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        model_expected = (
            (PostModelTest.group, self.group.title),
            (PostModelTest.post, 'Т' * POST_OBJECT_NAME_LENGHT)
        )
        for model, expected in model_expected:
            with self.subTest(model=model):
                self.assertEqual(str(model), expected)

    def test_verbose_name(self):
        """Проверяем, что verbose_name в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
            'image': 'Картинка'
        }
        for field, expected in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected)

    def test_help_text(self):
        """Проверяем, что help_text в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост',
            'image': 'Загрузите картинку'
        }
        for field, expected in help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected)


class FollowModelTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='follower')
        cls.author = User.objects.create_user(username='following')

    def test_unique_follow(self):
        """ Проверяем, что модель подписки создает уникальную запись
        """
        Follow.objects.create(user=self.user, author=self.author)
        subscrition_copy = Follow(user=self.user, author=self.author)
        with self.assertRaises(Exception) as raised:
            subscrition_copy.save()
        self.assertEqual(IntegrityError, type(raised.exception))
