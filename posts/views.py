from django.shortcuts import render, redirect, get_object_or_404
from .models import Post, Like, Comment
from .forms import PostForm, CommentForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count, Exists, OuterRef

@login_required
def feed(request):
    # annotate like_count and whether current user liked each post
    liked = Like.objects.filter(post=OuterRef('pk'), user=request.user)
    posts = Post.objects.annotate(
        like_count=Count('likes'),
        user_liked=Exists(liked),
    ).select_related('author__profile').prefetch_related('comments').order_by('-created_at')
    # pagination example (10 per page)
    from django.core.paginator import Paginator
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'posts/feed.html', {'page_obj': page_obj, 'post_form': PostForm(), 'comment_form': CommentForm()})

@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
    return redirect('feed')

@login_required
def like_post(request, post_id):
    # this is called by AJAX (POST)
    post = get_object_or_404(Post, id=post_id)
    like, created = Like.objects.get_or_create(user=request.user, post=post)
    if not created:
        # user already liked -> unlike
        like.delete()
        liked = False
    else:
        liked = True
    return JsonResponse({'liked': liked, 'likes_count': post.likes.count()})

@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.post = post
            comment.save()
    return redirect('feed')  # or redirect to post detail
