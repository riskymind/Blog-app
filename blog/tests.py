from django.test import TestCase, Client
from .models import Author, Tag, Post, Comment
from django.urls import reverse
from .forms import CommentForm


class StartingPageViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create an author
        author = Author.objects.create(first_name="test", last_name="testing", email_address="test@gmail.com")
        #  Create tags
        tag1 = Tag.objects.create(caption="Tag1")
        tag2 = Tag.objects.create(caption="Tag2")

        # Create 5 posts
        for i in range(5):
            post = Post.objects.create(
                title = f"Post Title {i}",
                excerpt = f"Post Excerpt {i}",
                image = "None",
                slug = f"post-title-{i}",
                content = "This is a valid post content",
                author = author
            )
            post.tags.add(tag1, tag2)
    
    def test_view_url_exists_at_desired_location(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
    
    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('index'))
        self.assertTemplateUsed(response, "blog/index.html")

    def test_content_data(self):
        response = self.client.get(reverse('index'))
        self.assertIn('posts', response.context)
        self.assertEqual(len(response.context['posts']), 3) # Check if only 3 post is displayed
    
    def test_queryset_ordering(self):
        response = self.client.get(reverse('index'))
        posts = response.context['posts']
        self.assertTrue(all(posts[i].date >= posts[i + 1].date for i in range(len(posts) - 1)))


class AllPostsViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create an author
        author = Author.objects.create(first_name="test", last_name="testing", email_address="test@gmail.com")
        
        # Create tags
        tag1 = Tag.objects.create(caption="Tag1")
        tag2 = Tag.objects.create(caption="Tag2")
        
        # Create 5 posts
        for i in range(5):
            post = Post.objects.create(
                title=f"Post Title {i}",
                excerpt=f"Post Excerpt {i}",
                image="None",  # Assuming you handle the absence of an image in your code
                slug=f"post-title-{i}",
                content="This is a valid post content",
                author=author,
            )
            post.tags.add(tag1, tag2)

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get('/posts')  
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('posts-page')) 
        self.assertTemplateUsed(response, 'blog/all-posts.html')

    def test_context_data(self):
        response = self.client.get(reverse('posts-page'))
        self.assertIn('posts', response.context)
        self.assertEqual(len(response.context['posts']), 5)  # All posts should be returned

    def test_queryset_ordering(self):
        response = self.client.get(reverse('posts-page'))
        posts = response.context['posts']
        self.assertTrue(all(posts[i].date >= posts[i + 1].date for i in range(len(posts) - 1)))


class SinglePostViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create an author
        cls.author = Author.objects.create(first_name="test", last_name="testing", email_address="test@gmail.com")

        # Create a tag
        cls.tag = Tag.objects.create(caption="Test Tag")

        # Create a post
        cls.post = Post.objects.create(
            title="Test Post",
            excerpt="Test excerpt",
            slug="test-post",
            content="This is test content for the post.",
            author=cls.author,
            image = "None"
        )
        cls.post.tags.add(cls.tag)

        # Create comments
        for i in range(3):
            Comment.objects.create(
                user_name=f"User {i}",
                user_email=f"user{i}@example.com",
                text=f"Test comment {i}",
                post=cls.post
            )

    def test_get_request(self):
        response = self.client.get(reverse("post-page-detail", args=[self.post.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "blog/post-detail.html")
        self.assertEqual(response.context["post"], self.post)
        self.assertEqual(len(response.context["post_tags"]), 1)
        self.assertIsInstance(response.context["comment_form"], CommentForm)
        self.assertEqual(len(response.context["comments"]), 3)
        self.assertFalse(response.context["saved_for_later"])  # Default session is empty

    def test_get_request_with_saved_post(self):
        session = self.client.session
        session["stored_posts"] = [self.post.id]
        session.save()

        response = self.client.get(reverse("post-page-detail", args=[self.post.slug]))
        self.assertTrue(response.context["saved_for_later"])

    def test_post_request_valid_form(self):
        response = self.client.post(
            reverse("post-page-detail", args=[self.post.slug]),
            data={
                "user_name": "New User",
                "user_email": "newuser@example.com",
                "text": "This is a new comment",
            }
        )
        self.assertEqual(response.status_code, 302)  # Redirection
        self.assertEqual(response["Location"], reverse("post-page-detail", args=[self.post.slug]))
        self.assertEqual(Comment.objects.filter(post=self.post).count(), 4)  # 1 new comment added

    def test_post_request_invalid_form(self):
        response = self.client.post(
            reverse("post-page-detail", args=[self.post.slug]),
            data={
                "user_name": "",  # Invalid as the name field is required
                "user_email": "invalid_email",  # Invalid email format
                "text": "",
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "blog/post-detail.html")
        self.assertIsInstance(response.context["comment_form"], CommentForm)
        self.assertTrue(response.context["comment_form"].errors)  # Form should contain errors
        self.assertEqual(Comment.objects.filter(post=self.post).count(), 3)  # No new comment added


class ReadLaterViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create an author
        cls.author = Author.objects.create(first_name="test", last_name="testing", email_address="test@gmail.com")
        
        # Create tags
        cls.tag1 = Tag.objects.create(caption="Django")
        cls.tag2 = Tag.objects.create(caption="Testing")
        
        # Create posts
        cls.post1 = Post.objects.create(
            title="First Post",
            excerpt="Excerpt for first post",
            slug="first-post",
            content="Content for the first post.",
            author=cls.author,
            image = "None"
        )
        cls.post1.tags.add(cls.tag1, cls.tag2)
        
        cls.post2 = Post.objects.create(
            title="Second Post",
            excerpt="Excerpt for second post",
            slug="second-post",
            content="Content for the second post.",
            author=cls.author,
            image = "None"
        )
        cls.post2.tags.add(cls.tag1)
        
        cls.post3 = Post.objects.create(
            title="Third Post",
            excerpt="Excerpt for third post",
            slug="third-post",
            content="Content for the third post.",
            author=cls.author,
            image = "None"
        )
        cls.post3.tags.add(cls.tag2)
        
    def setUp(self):
        self.client = Client()
        self.read_later_url = reverse('read-later')  # Replace with your actual URL name

    def test_get_read_later_no_posts(self):
        response = self.client.get(self.read_later_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "blog/stored-post.html")
        self.assertIn('posts', response.context)
        self.assertIn('has_post', response.context)
        self.assertFalse(response.context['has_post'])
        self.assertEqual(len(response.context['posts']), 0)

    def test_get_read_later_with_posts(self):
        # Add post1 and post2 to stored_posts in session
        session = self.client.session
        session['stored_posts'] = [self.post1.id, self.post2.id]
        session.save()
        
        response = self.client.get(self.read_later_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "blog/stored-post.html")
        self.assertIn('posts', response.context)
        self.assertIn('has_post', response.context)
        self.assertTrue(response.context['has_post'])
        self.assertEqual(list(response.context['posts']), [self.post1, self.post2])

    def test_post_add_post_to_read_later(self):
        # Initially, stored_posts is empty
        response = self.client.post(self.read_later_url, data={'post_id': self.post3.id})
        self.assertEqual(response.status_code, 302)  # Redirect status
        self.assertEqual(response.url, "/")  # Redirect to homepage
        
        # Verify that post3.id is in stored_posts
        session = self.client.session
        self.assertIn('stored_posts', session)
        self.assertIn(self.post3.id, session['stored_posts'])

    def test_post_remove_post_from_read_later(self):
        # Add post1 to stored_posts first
        session = self.client.session
        session['stored_posts'] = [self.post1.id]
        session.save()
        
        # Now, send POST request to remove post1
        response = self.client.post(self.read_later_url, data={'post_id': self.post1.id})
        self.assertEqual(response.status_code, 302)  # Redirect status
        self.assertEqual(response.url, "/")  # Redirect to homepage
        
        # Verify that post1.id is removed from stored_posts
        session = self.client.session
        self.assertIn('stored_posts', session)
        self.assertNotIn(self.post1.id, session['stored_posts'])

    def test_post_invalid_post_id(self):
        # Send POST request with a non-existent post_id
        invalid_post_id = 9999  # Assuming this ID doesn't exist
        response = self.client.post(self.read_later_url, data={'post_id': invalid_post_id})
        
        # Depending on your view's implementation, this might raise an error or handle gracefully
        # Here, we'll assume it redirects as usual
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")
        
        # Verify that invalid_post_id is not added to stored_posts
        session = self.client.session
        self.assertIn('stored_posts', session)
        # self.assertNotIn(invalid_post_id, session['stored_posts'])

    def test_get_read_later_with_all_posts(self):
        # Add all posts to stored_posts in session
        session = self.client.session
        session['stored_posts'] = [self.post1.id, self.post2.id, self.post3.id]
        session.save()
        
        response = self.client.get(self.read_later_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "blog/stored-post.html")
        self.assertIn('posts', response.context)
        self.assertIn('has_post', response.context)
        self.assertTrue(response.context['has_post'])
        self.assertEqual(
            list(response.context['posts']),
            [self.post1, self.post2, self.post3]
        )

# Test the Blog App Models
class BlogModelTests(TestCase):
    def setUp(self):
        # Create tags
        self.tag1 = Tag.objects.create(caption="Django")
        self.tag2 = Tag.objects.create(caption="Python")

        # Create an author
        self.author = Author.objects.create(
            first_name="John",
            last_name="Doe",
            email_address="john.doe@example.com"
        )

        # Create a post
        self.post = Post.objects.create(
            title="Test Post",
            excerpt="This is a test excerpt.",
            image="test_image.jpg",
            slug="test-post",
            content="This is the content of the test post.",
            author=self.author
        )
        self.post.tags.add(self.tag1, self.tag2)

        # Add a comment to the post
        self.comment = Comment.objects.create(
            user_name="Jane Smith",
            user_email="jane.smith@example.com",
            text="This is a test comment.",
            post=self.post
        )

    def test_author_full_name(self):
        self.assertEqual(self.author.full_name(), "John Doe")

    def test_post_str(self):
        self.assertEqual(str(self.post), "Test Post")

    def test_tag_str(self):
        self.assertEqual(str(self.tag1), "Django")

    def test_comment_str(self):
        self.assertEqual(self.comment.text, "This is a test comment.")

    def test_post_has_tags(self):
        tags = self.post.tags.all()
        self.assertIn(self.tag1, tags)
        self.assertIn(self.tag2, tags)

    def test_post_author(self):
        self.assertEqual(self.post.author, self.author)

    def test_comment_association_with_post(self):
        self.assertEqual(self.comment.post, self.post)


# Testing the comment Form
class CommentFormTests(TestCase):
    def setUp(self):
        # Sample valid data for the form
        self.valid_data = {
            "user_name": "Jane Doe",
            "user_email": "jane.doe@example.com",
            "text": "This is a test comment."
        }

        # Sample invalid data
        self.invalid_data_missing_name = {
            "user_name": "",
            "user_email": "jane.doe@example.com",
            "text": "This is a test comment."
        }
        self.invalid_data_invalid_email = {
            "user_name": "Jane Doe",
            "user_email": "invalid-email",
            "text": "This is a test comment."
        }

    def test_form_valid_data(self):
        form = CommentForm(data=self.valid_data)
        self.assertTrue(form.is_valid())  # Form should be valid with valid data
        comment = form.save(commit=False)  # Test that form saves correctly
        self.assertEqual(comment.user_name, "Jane Doe")
        self.assertEqual(comment.user_email, "jane.doe@example.com")
        self.assertEqual(comment.text, "This is a test comment.")

    def test_form_missing_name(self):
        form = CommentForm(data=self.invalid_data_missing_name)
        self.assertFalse(form.is_valid())  # Form should be invalid
        self.assertIn("user_name", form.errors)  # Check if error exists for user_name

    def test_form_invalid_email(self):
        form = CommentForm(data=self.invalid_data_invalid_email)
        self.assertFalse(form.is_valid())  # Form should be invalid
        self.assertIn("user_email", form.errors)  # Check if error exists for user_email

    def test_form_labels(self):
        form = CommentForm()
        self.assertEqual(form.fields["user_name"].label, "Your Name")
        self.assertEqual(form.fields["user_email"].label, "Your Email")
        self.assertEqual(form.fields["text"].label, "Your Comment")
