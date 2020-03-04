from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from posts.models import Post, Group, User, Comment, Follow
from django.core.paginator import Paginator
from .forms import PostForm, CommentForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page


def index(request):
    post_list = Post.objects.order_by('-pub_date').all()
    favorites = Follow.objects.filter(user=request.user).count()
    if request.user.is_authenticated and favorites > 0 :
        follow = True
    else:
        follow = False
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html', {'page': page, 'paginator': paginator, 'follow': follow})

def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = Post.objects.filter(group=group).order_by('-pub_date')[:12]
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "group.html", {"group": group, 'page': page, 'paginator': paginator})

@login_required
def new_post(request):
    button_called = 'Создать'
    title = "Создание поста"
    if request.method == 'POST':
        form = PostForm(request.POST or None, files=request.FILES or None)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('index')
    form = PostForm()
    return render(request, 'new.html', {'form': form, 'button_called': button_called, 'title': title})

def profile(request, username):
    profile = get_object_or_404(User, username=username)
    profile_post_list = Post.objects.filter(author=profile).order_by('-pub_date').all()
    favorite = Follow.objects.filter(user=request.user, author=profile).count()
    if request.user.is_authenticated and favorite > 0:
        following = True
    else:
        following = False
    posts_count = profile_post_list.count()
    paginator = Paginator(profile_post_list, 5)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'profile.html', {'profile': profile, 'page': page, 'paginator': paginator, 'posts_count': posts_count, 'following': following})

def post_view(request, username, post_id):
    profile = get_object_or_404(User, username=username)
    profile_post_list = Post.objects.filter(author=profile).order_by('-pub_date').all()
    posts_count = profile_post_list.count()
    post = get_object_or_404(Post, pk=post_id)
    comments = Comment.objects.filter(post=post).all()
    form = CommentForm()
    return render(request, 'post.html', {'post': post, "profile": profile, 'posts_count': posts_count, 'form': form, 'items': comments})#

def post_edit(request, username, post_id):
    profile = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, pk=post_id, author=profile)
    if request.user != profile:
        return redirect('post_view', username=username, post_id=post_id)
    button_called = "Редактировать"
    title = 'Редактирование поста'
    if request.method == 'POST':
        form = PostForm(request.POST or None, files=request.FILES or None, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('post_view', username=username, post_id=post_id)
    form = PostForm(instance=post)
    return render(request, 'new.html', {'form': form, 'button_called': button_called, 'title': title, 'username': username, 'post': post})


def page_not_found(request, exception):
    return render(request, "misc/404.html", {'path': request.path}, status = 404)


def server_error(request):
    return render(request, 'misc/500.html', status = 500)

@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id,)
    if request.method == 'POST':
        form=CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
            return redirect('post_view', username = post.author.username, post_id = post_id)
    form = CommentForm()
    return redirect('post_view', username = post.author.username, post_id = post_id)

@login_required
def follow_index(request):
        #follow = Follow.objects.get(user=request.user)
        #follow_list = Follow.objects.select_related('author', 'user').filter(user=request.user)#Список тех, на кого подписан юзер
       # author_list = []
        #for favorite in follow_list:
            #author_list.append(favorite.author)
        post_list = Post.objects.filter(author__following__user=request.user).select_related('author').order_by('-pub_date').all()
        paginator = Paginator(post_list, 10)
        page_number = request.GET.get('page')
        page = paginator.get_page(page_number)
        return render(request, "follow.html", {'page': page, 'paginator': paginator})

@login_required
def profile_follow(request, username):
        follow = User.objects.get(username=username)#Тот, на кого подписываются
        follower = User.objects.get(username=request.user.username)#Тот, кто подписывается
        Follow.objects.create(user=follower, author=follow)
        return redirect('follow_index')


@login_required
def profile_unfollow(request, username):
        follow = User.objects.get(username=username)#Тот, на кого подписываются
        follower = User.objects.get(username=request.user.username)#Тот, кто подписывается
        Follow.objects.filter(user=follower, author=follow).delete()
        return redirect('follow_index')
