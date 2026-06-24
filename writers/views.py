from django.contrib.auth.models import User
from django.shortcuts import render, redirect , get_object_or_404
from accounts.models import Profile
from worries.models import Worry, Answer
from writers.models import Epilogue
from main.utils import Yang, edit_points
from .models import *

# Create your views here.

def get_profile_context(user):
    profile = get_object_or_404(Profile, writer=user)
    return {
        "profile": profile,
        "worry_count": profile.worry_count,
        "points": profile.points,
    }

"""
    [마이페이지 함수]
    - 기능 : 내 정보, 내 활동 정보들 한눈에 리스트 확인 가능
    - 가져오는 정보 : User, Profile
    - 연결 페이지 : 양 성장과정 구매, 내 고민, 내 답변, 포인트 이용내역, 북마크
    - return : mypage.html 화면 표시
    * 유의사항 : 로그인 하지 않고 마이페이지 들어가면 로그인 페이지로 넘어감 *
"""

def mypage(request):

    if not request.user.is_authenticated:
        return redirect("accounts:login")   # 비로그인 시, 로그인 페이지로 넘어감

    profile = get_object_or_404(Profile, writer=request.user)
    yang_img = Yang[profile.current_yang]["image"]

    context = {
        'profile_writer' : request.user,
        'profile' : profile,
        'yang_img' : yang_img,
    }

    return render(request, 'writers/mypage.html', context)


"""
    [내 고민 함수]
    - 기능 : 본인이 작성한 고민들 고민배송중/공개O/공개X 로 나누어서 볼 수 있음
    - 가져오는 정보 : Worry
    - return : my_worry.html 화면 표시
"""

def my_worry(request):
    
    if not request.user.is_authenticated:
        return redirect("accounts:login")   # 비로그인 시, 로그인 페이지로 넘어감

    profile_context = get_profile_context(request.user)

    delivery_worries = Worry.objects.filter(    # 고민 배송 중
        writer = request.user,
        is_complete = False,
        is_delete = False
    )
    public_worries = Worry.objects.filter(      # 공개 O
        writer = request.user, 
        is_complete = True, 
        is_HoF=True,
        is_delete = False
    )
    private_worries = Worry.objects.filter(     # 공개 X
        writer = request.user,
        is_complete = True,
        is_HoF = False,
        is_delete = False
    )

    context = {
        **profile_context,
        'delivery_worries' : delivery_worries,
        'public_worries' : public_worries,
        'private_worries' : private_worries,
    }

    return render(request, 'writers/my_worry.html', context)

"""
    [내 고민 상세 분기 함수]
    - 기능 : 고민 완료 여부에 따라 배송 중/배송 완료 상세 화면으로 이동
    - 받는 값 : worry_id
    - return : 배송 중 또는 배송 완료 상세 화면으로 리다이렉트
"""
def my_worry_detail(request, worry_id):
    if not request.user.is_authenticated:
        return redirect("accounts:login")

    worry = get_object_or_404(Worry, pk=worry_id, writer=request.user, is_delete=False)

    if worry.is_complete:
        return redirect("writers:worry_completed", worry_id=worry.id)

    return redirect("writers:worry_ing", worry_id=worry.id)

"""
    [배송 중 고민 상세 함수]
    - 기능 : 아직 완료되지 않은 고민과 도착한 답변을 조회
    - 받는 값 : worry_id
    - return : worry_ing.html 화면 표시
"""
def worry_ing(request, worry_id):
    if not request.user.is_authenticated:
        return redirect("accounts:login")

    worry = get_object_or_404(Worry, pk=worry_id, writer=request.user, is_delete=False)

    if worry.is_complete:
        return redirect("writers:worry_completed", worry_id=worry.id)

    answers = Answer.objects.filter(worry=worry).select_related("writer")

    context = {
        "worry": worry,
        "answers": answers,
        "has_answers": answers.exists(),
    }

    return render(request, "writers/worry_ing.html", context)

"""
    [배송 완료 고민 상세 함수]
    - 기능 : 완료된 고민과 답변, 후일담을 공개/비공개/후일담 유무에 따라 조회
    - 받는 값 : worry_id
    - return : worry_complete.html 화면 표시
"""
def worry_completed(request, worry_id):
    if not request.user.is_authenticated:
        return redirect("accounts:login")

    worry = get_object_or_404(Worry, pk=worry_id, writer=request.user, is_delete=False)

    if not worry.is_complete:
        return redirect("writers:worry_ing", worry_id=worry.id)

    answers = Answer.objects.filter(worry=worry).select_related("writer")
    epilogue = Epilogue.objects.filter(worry=worry, ep_is_delete=False).first()

    context = {
        "worry": worry,
        "answers": answers,
        "epilogue": epilogue,
        "is_public_epilogue": worry.is_HoF,
        "has_epilogue": epilogue is not None,
    }

    return render(request, "writers/worry_complete.html", context)

"""
    [내 고민 삭제 함수]
    - 기능 : 내 고민을 삭제 상태로 변경
    - 받는 값 : worry_id
    - return : 내 고민 목록으로 리다이렉트
"""
def delete_worry(request, worry_id):
    if not request.user.is_authenticated:
        return redirect("accounts:login")

    worry = get_object_or_404(Worry, pk=worry_id, writer=request.user, is_delete=False)

    if request.method == "POST":
        worry.is_delete = True
        worry.save()

    return redirect("writers:my_worry")


"""
    [내 답변 리스트 함수]
    - 기능 : 본인이 작성한 답변들을 볼 수 있음
    - 가져오는 정보 : Answer
    - return : demo_my_answer_list.html 화면 표시
    * 유의사항 : 정렬은 최신순으로 *
"""

def my_answer_list(request):

    if not request.user.is_authenticated:
        return redirect("accounts:login")   # 비로그인 시, 로그인 페이지로 넘어감
    
    my_answers_list = Answer.objects.filter(writer = request.user).order_by("-pub_date")  # 내 답변 최신순으로 정렬

    context = {
        **get_profile_context(request.user),
        'my_answers_list' : my_answers_list,
    }

    return render(request, 'writers/my_answer_list.html', context)

"""
    [내 답변 상세 함수]
    - 기능 : 내 답변 목록에서 선택한 답변이 포함된 고민-답변-후일담 상세 화면 조회
    - 가져오는 정보 : Answer
    - return : my_answer.html 화면 표시
"""
def my_answer_detail(request, answer_id):
    if not request.user.is_authenticated:
        return redirect("accounts:login")

    answer = get_object_or_404(Answer, pk=answer_id, writer=request.user)
    worry = answer.worry

    answers = Answer.objects.filter(worry=worry).select_related("writer")
    epilogue = Epilogue.objects.filter(worry=worry).first()

    context = {
        "selected_answer": answer,
        "worry": worry,
        "answers": answers,
        "epilogue": epilogue,
    }

    return render(request, "writers/my_answer.html", context)


"""
    [북마크 함수]
    - 기능 : 본인이 누른 북마크들을 볼 수 있음
    - 가져오는 정보 : Worry
    - return : worry_bookmark.html 화면 표시
    
    * 유의사항 : 현재 후일담 북마크가 없어서 고민 북마크만 넣어둠. 추후에 반영 예정 *
    -> 반영 완료!!
"""

def worry_bookmark(request):

    if not request.user.is_authenticated:
        return redirect("accounts:login")   # 비로그인 시, 로그인 페이지로 넘어감
    
    worry_bookmarks = Worry.objects.filter(later_answer = request.user)     # 고민 북마크
    epilogue_bookmark = Epilogue.objects.filter(later_check = request.user)       # 후일담 북마크

    context = {
        **get_profile_context(request.user),
        'worry_bookmarks' : worry_bookmarks,
        'epilogue_bookmark' : epilogue_bookmark,
    }

    return render(request, 'writers/worry_bookmark.html', context)

"""
    [후일담 작성]
    - 기능 : 후일담 작성 및 공개 여부 설정
    - 받는 값 : worry_id, ep_han_madi, ep_title, ep_content, is_HoF
    - return : 성공 -> 홈 화면 이동 / 실패 -> 로그인 화면 이동

    * 유의사항 *
    - 고민 작성자만 후일담 작성 가능
    - 공개 O 선택 시 is_HoF = True
    - 공개 X 선택 시 is_HoF = False
"""
def post_epilogue(request, worry_id):
    if not request.user.is_authenticated:
        return redirect("accounts:login")

    worry = get_object_or_404(Worry, pk=worry_id)

    # 현재 사용자 == 고민 작성자인지 검증
    if request.user != worry.writer:
        return redirect("main:home")

    profile = get_object_or_404(Profile, writer=request.user)

    old_epilogue = Epilogue.objects.filter(worry=worry).first()
    if old_epilogue is not None:
        return redirect("main:go_epilogue", epilogue_id=old_epilogue.id)

    # 1단계: worry_answer.html에서 "후일담 작성하기" 눌렀을 때
    # 아직 ep_title, ep_content 등이 없으므로 저장하지 말고 작성 화면만 보여줌
    if request.method == "POST" and "ep_title" not in request.POST:
        selected_answer_ids = request.POST.getlist("answer_ids")

        context = {
            "worry": worry,
            "selected_answer_ids": selected_answer_ids,
            "worry_count": profile.worry_count,
            "points": profile.points,
        }

        return render(request, "writers/post_epilogue.html", context)

    # GET으로 직접 들어온 경우도 작성 화면 보여주기
    if request.method == "GET":
        context = {
            "worry": worry,
            "selected_answer_ids": [],
            "worry_count": profile.worry_count,
            "points": profile.points,
        }

        return render(request, "writers/post_epilogue.html", context)

    # 2단계: post_epilogue.html에서 "후일담 제출하기" 눌렀을 때 실제 저장
    worry.is_HoF = (request.POST.get("is_HoF") == "True")
    worry.is_complete = True
    worry.save()

    new_epilogue = Epilogue()
    new_epilogue.worry = worry
    new_epilogue.writer = request.user
    new_epilogue.ep_han_madi = request.POST.get("ep_han_madi", "")
    new_epilogue.ep_title = request.POST.get("ep_title", "")
    new_epilogue.ep_content = request.POST.get("ep_content", "")
    new_epilogue.save()

    edit_points(profile, "후일담 작성", 2)

    selected_answers_ids = request.POST.getlist("answer_ids")

    selected_answers = Answer.objects.filter(
        id__in=selected_answers_ids,
        worry=worry
    )

    for answer in selected_answers:
        if answer.writer is not None:
            new_epilogue.visible_users.add(answer.writer)

    request.session["show_epilogue_popup_id"] = new_epilogue.id

    return redirect("main:home_from_post_epilogue", epilogue_id=new_epilogue.id)

"""
    [후일담 북마크 등록/취소 함수]
    - 기능 : 후일담 북마크 등록/삭제
    - 가져오는 정보 : Epilogue
    - return : 성공 -> 명예의 전당 화면으로 전환
"""
def ep_bookmark(request, epilogue_id):

    if not request.user.is_authenticated:
        return redirect("accounts:login")   # 비로그인 시, 로그인 페이지로 넘어감

    epilogue = get_object_or_404(Epilogue, pk=epilogue_id, ep_is_delete=False)

    if request.method == "POST":
        if request.user in epilogue.later_check.all():
            epilogue.later_check.remove(request.user)
        else:
            epilogue.later_check.add(request.user)

    next_url = request.POST.get("next")
    if next_url:
        return redirect(next_url)

    return redirect("worries:hall_of_fame")


"""
    [후일담 공감 도장 등록/취소 함수]
    - 기능 : 후일담 공감 도장 등록/삭제
    - 가져오는 정보 : Epilogue
    - return : 성공 -> 명예의 전당 화면으로 전환
    * 유의사항 : 해당 worry story로 전환하는게 맞을까?*
"""
def post_epilogue_gonggam(request, epilogue_id):
    if not request.user.is_authenticated:
        return redirect("accounts:login")
    
    epilogue = get_object_or_404(Epilogue, pk=epilogue_id)

    if request.user in epilogue.ep_gonggam.all():   # 공감버튼이 이미 눌려있는 경우 -> 취소
        epilogue.ep_gonggam.remove(request.user)
        epilogue.ep_gonggam_count -= 1

    else:                                           # 공감버튼 안 눌려있는 경우 -> 눌림
        epilogue.ep_gonggam.add(request.user)
        epilogue.ep_gonggam_count += 1

    epilogue.save()

    return redirect("worries:hall_of_fame")


"""
    [고민-답변-후일담 함수]
    - 기능 : 하나의 고민에 대한 답변, 후일담 전체 보기 가능
    - 가져오는 정보 : Worry, Answer, Epilogue
    - return : demo_worry_story.html 화면 표시
    
    * 유의사항*
    - 공개 O : 모든 사용자 조회 가능
    - 공개 X : 고민 작성자와 해당 고민에 답변한 사람들만 조회 가능
"""

def worry_story(request, worry_id, source):
    worry = get_object_or_404(Worry, pk=worry_id)

    if request.user == worry.writer:    # 답변 안읽음 표시 지움
        worry.hit = 1
        worry.save()

    if not worry.is_HoF:    # 공개X -> 고민 작성자와 해당 고민에 답변을 한 사람들만 조회 가능                  
        is_writer = (request.user == worry.writer)

        is_answerer = Answer.objects.filter(worry=worry, writer=request.user).exists()

        if not is_writer and not is_answerer:
            return redirect("main:home")
        
    answers = Answer.objects.filter(worry=worry)
    epilogue = Epilogue.objects.filter(worry=worry)

    context = {
        'worry' : worry,
        'answers' : answers,
        'epilogue' : epilogue,
        'source' : source,
    }

    return render(request, 'writers/worry_story.html', context)

"""
    [고민 답변 확인 함수]
    - 기능: 고민-답변들 확인
    - 받는 값: worry_id
    - return: 성공 -> worry_answer.html 렌더링 / 실패(인증 에러) -> 로그인으로 리다이렉트
"""
def get_worry_answer(request, worry_id):
    if not request.user.is_authenticated:
        return redirect("accounts:login")

    profile = get_object_or_404(Profile, writer=request.user)

    worry = get_object_or_404(
        Worry,
        id=worry_id,
        writer=request.user,
        is_delete=False
    )

    answers = Answer.objects.filter(worry=worry).order_by("id")

    context = {
        "worry": worry,
        "answers": answers,
        "worry_count": profile.worry_count,
        "points": profile.points,
    }

    return render(request, "writers/worry_answer.html", context)

"""
    [포인트 이용 내역 화면 렌더링]
    - 기능: 포인트 이용 내역 화면 렌더링
    - 받는 값: X
"""
def get_point_logs(request):
    if not request.user.is_authenticated:
        return redirect("accounts:login")

    point_logs = PointLog.objects.filter(
        writer=request.user
    )
    profile = get_object_or_404(Profile, writer=request.user)
    
    yang = Yang[profile.current_yang]
    yang_name = yang["name"]
    yang_img = yang["image"]
    
    context = {
        "profile": profile,
        "worry_count": profile.worry_count,
        "points": profile.points,
        "point_logs": point_logs,
        "yang_img": yang_img,
        "yang_name": yang_name,
    }

    return render(request, "writers/point_logs.html", context)

def my_worry_detail(request, worry_id):
    if not request.user.is_authenticated:
        return redirect("accounts:login")

    profile = get_object_or_404(Profile, writer=request.user)

    worry = get_object_or_404(
        Worry,
        pk=worry_id,
        writer=request.user,
        is_delete=False
    )

    answers = Answer.objects.filter(worry=worry).order_by("id")

    context = {
        "worry": worry,
        "answers": answers,
        "worry_count": profile.worry_count,
        "points": profile.points,
    }

    return render(request, "writers/worry_answer.html", context)


def worry_ing(request, worry_id):
    return my_worry_detail(request, worry_id)


def worry_completed(request, worry_id):
    return worry_story(request, worry_id, "worry")


def delete_worry(request, worry_id):
    if not request.user.is_authenticated:
        return redirect("accounts:login")

    worry = get_object_or_404(
        Worry,
        pk=worry_id,
        writer=request.user
    )

    worry.is_delete = True
    worry.save()

    return redirect("writers:my_worry")


def my_answer_detail(request, answer_id):
    if not request.user.is_authenticated:
        return redirect("accounts:login")

    answer = get_object_or_404(
        Answer,
        pk=answer_id,
        writer=request.user
    )

    return redirect("writers:worry_story", worry_id=answer.worry.id)
