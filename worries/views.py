from django.shortcuts import render, redirect, get_object_or_404
from writers.models import Epilogue
from accounts.models import Profile
from .models import *
from main.utils import get_time_ago, edit_points

"""
[고민 작성]
- 기능: 작성한 내용으로 Worry 객체 생성 및 저장
- 받는 값: keyword, title, content, mbti
- return: 성공 -> home 리다이렉트 / 실패(인증 에러) -> 로그인 메서드로 리다이렉트
"""
def post_worry(request):
    if not request.user.is_authenticated:
        return redirect("accounts:login")
    
    profile = get_object_or_404(Profile, writer=request.user)
    
    # 잔여 고민 작성 가능 개수 확인
    if profile.worry_count <= 0:
        return redirect("main:home")
    
    if request.method == "POST":
        new_worry = Worry()

        new_worry.writer = request.user
        new_worry.keyword = request.POST["keyword"]
        new_worry.title = request.POST["title"]
        new_worry.content = request.POST["content"]
        new_worry.mbti = request.POST["mbti"]

        new_worry.save()

        profile.worry_count -= 1
        profile.save()

        return redirect("main:home")

    return render(request, "worries/post_worry.html")

"""
[고민 리스트 조회]
- 기능: 모든 고민글을 반환
- 받는 값: X
- return: 모든 Worry 객체
"""
def get_worries(request):
    if not request.user.is_authenticated:
        return redirect("accounts:login")

    profile = get_object_or_404(Profile, writer=request.user)
    worry_count = profile.worry_count
    points = profile.points

    worries_per_page = 6 # 한 페이지 당 보여줄 고민 개수
    page = request.GET.get("page", "1") # 현재 페이지 번호 가져오기

    if page.isdigit():
        page = int(page)
    else:
        page = 1

    if page < 1:
        page = 1

    # 고민 리스트 조회
    worries = Worry.objects.filter(
    writer=request.user,
    is_delete=False
).order_by("-pub_date")

    # 전체 고민 개수
    total_count = worries.count()

    # 전체 페이지 수 계산
    if total_count == 0:
        total_page = 1
    else:
        total_page = (total_count + worries_per_page - 1) // worries_per_page

    if page > total_page: # 현재 페이지가 전체 페이지보다 크면 마지막 페이지로
        page = total_page

    # 페이지에 해당하는 고민 리스트 가져오기
    start = (page - 1) * worries_per_page
    end = start + worries_per_page
    worries_in_page = worries[start:end]

    worry_items = []
    for worry in worries_in_page:   # 작성 경과 시간 함께 묶어서 제공
        worry_items.append({
            "worry": worry,
            "time_ago": get_time_ago(worry.pub_date),
            "cheerup_count": worry.cheerup_count,
            "answer_count": Answer.objects.filter(worry=worry).count(),
            "is_bookmarked": request.user in worry.later_answer.all(),
        })

    # 하단에 출력할 페이지 번호 리스트
    page_numbers = []
    number = page

    while number <= page + 2 and number <= total_page:
        page_numbers.append(number)
        number += 1
        
    context = {
        "worry_count": worry_count,
        "points": points,

        "worries": worry_items,

        "page": page,
        "total_page": total_page,
        
        "has_prev": page > 1,
        "has_next": page < total_page,
        
        "prev_page": page - 1,
        "next_page": page + 1,
        "page_numbers": page_numbers,
    }

    return render(request, "worries/list.html", context)


"""
[우체통 렌더링]
- 기능: 모든 고민글을 반환
- 받는 값: X
- return: 모든 Worry 객체
"""
def postbox(request):
    if not request.user.is_authenticated:
        return redirect("accounts:login")

    profile = get_object_or_404(Profile, writer=request.user)
    worry_count = profile.worry_count
    points = profile.points

    worries_per_page = 6
    page = request.GET.get("page", "1")

    if page.isdigit():
        page = int(page)
    else:
        page = 1

    if page < 1:
        page = 1

    # 우체통에서는 내가 쓴 고민만 보여줌
    worries = Worry.objects.filter(
        writer=request.user,
        is_delete=False
    ).order_by("-pub_date")

    total_count = worries.count()

    if total_count == 0:
        total_page = 1
    else:
        total_page = (total_count + worries_per_page - 1) // worries_per_page

    if page > total_page:
        page = total_page

    start = (page - 1) * worries_per_page
    end = start + worries_per_page
    worries_in_page = worries[start:end]

    worry_items = []

    for worry in worries_in_page:
        worry_items.append({
            "worry": worry,
            "time_ago": get_time_ago(worry.pub_date),
            "cheerup_count": worry.cheerup_count,
            "answer_count": Answer.objects.filter(worry=worry).count(),
        })

    page_numbers = []
    number = page

    while number <= page + 2 and number <= total_page:
        page_numbers.append(number)
        number += 1

    context = {
        "worry_count": worry_count,
        "points": points,
        "worries": worry_items,
        "page": page,
        "total_page": total_page,
        "has_prev": page > 1,
        "has_next": page < total_page,
        "prev_page": page - 1,
        "next_page": page + 1,
        "page_numbers": page_numbers,
    }

    return render(request, "worries/postbox.html", context)


"""
[고민 북마크 등록/취소]
- 기능: 나중에 답변할 고민 북마크를 추가/삭제
- 받는 값: worry_id
- return: 성공 시 -> 기존 화면(고민 리스트)으로 리다이렉트
""" 
def post_bookmark(request, worry_id):
    if not request.user.is_authenticated:
        return redirect("accounts:login")

    worry = get_object_or_404(Worry, pk=worry_id)

    if request.method == "POST":
        if request.user in worry.later_answer.all():
            worry.later_answer.remove(request.user)
        else:
            worry.later_answer.add(request.user)
        
        worry.save()
    
    next_url = request.POST.get("next")

    if next_url:
        return redirect(next_url)

    return redirect("worries:get_worries")

"""
[고민 응원 도장 등록/취소]
- 기능: 고민에 대해 응원 도장 추가/삭제
- 받는 값: worry_id
- return: 성공 시 -> 기존 화면(고민 리스트)으로 리다이렉트
"""
def post_cheerup(request, worry_id):
    if not request.user.is_authenticated:
        return redirect("accounts:login")

    worry = get_object_or_404(Worry, pk=worry_id)

    if request.user in worry.cheerup.all():
        worry.cheerup.remove(request.user)
        worry.cheerup_count = max(0, worry.cheerup_count - 1)
        
    else:
        worry.cheerup.add(request.user)
        worry.cheerup_count += 1

    worry.save()

    next_url = request.POST.get("next")
    if next_url:
        return redirect(next_url)
    
    return redirect("worries:get_worries")

"""
[고민 상세 화면 리다이렉트]
- 기능: 고민 상세 화면으로 이동
- 받는 값: worry_id
- return: 성공 시 -> 고민 상세 화면으로 리다이렉트
"""
def get_worry_detail(request, worry_id):
    if not request.user.is_authenticated:
        return redirect("accounts:login")

    profile = get_object_or_404(Profile, writer=request.user)
    worry = get_object_or_404(Worry, pk=worry_id)

    is_bookmarked = request.user in worry.later_answer.all()

    context = {
        "worry": worry,
        "worry_count": profile.worry_count,
        "points": profile.points,
        "is_bookmarked": is_bookmarked,
    }

    return render(request, "worries/worry_detail.html", context)

"""
[고민 답변 작성]
- 기능: POST-고민 답변 작성 / GET-고민 답변 작성 화면 이동
- 받는 값: worry_id + (POST의 경우: situation, my_action, recommendation)
- return: GET 성공 시 -> 고민 답변 작성 화면 렌더링 / POST 성공 시 -> 메인 화면 리다이렉트 / 실패 시 -> 로그인 화면 이동

* 유의사항 *
- 답변은 최대 5개까지만 작성 가능
"""
def post_answer(request, worry_id):
    if not request.user.is_authenticated:
        return redirect("accounts:login")

    worry = get_object_or_404(Worry, pk=worry_id)

    # 자기 고민에는 답변 불가
    if request.user == worry.writer:
        return redirect("worries:get_worry_detail", worry.id)

    answer_count = Answer.objects.filter(worry=worry).count()
    
    
    if answer_count >= 5:       # 답변 5개 초과 시 
        return redirect("worries:get_worry_detail", worry.id)
    
    # 고민 답변 작성 후 제출
    if request.method == "POST":

        answer = Answer()
        answer.worry = worry
        answer.writer = request.user
        answer.situation = request.POST["situation"]
        answer.my_action = request.POST["my_action"]
        answer.recommendation = request.POST["recommendation"]

        answer.save()

        worry.hit = 0   # 답변 안읽음 표시
        worry.save()

        return redirect("main:home")

    # 고민 답변 작성 화면 이동
    else:
        context = {
            "answer_user": request.user,
            "worry_writer": worry.writer.profile,
            "worry": worry,
        }
        return render(request, "worries/write_answer.html", context)

"""
    [명예의 전당 리스트 함수]
    - 기능 : 명예의 전당에 공개된 고민들 리스트 조회
    - 받는 값 : Worry
    - return : hof_list.html 화면 표시 
    * 유의사항 : 후일담 공감도장 많은 순으로 정렬  *
"""

def hall_of_fame(request):
    
    hof_worries = Worry.objects.filter(is_HoF = True).order_by("-epilogue__ep_gonggam_count")   # 명예의 전당에 공개된 고민만 조회 가능

    context = {
        'hof_worries' : hof_worries,
    }

    if request.user.is_authenticated:
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            profile = None

        if profile is not None:
            context.update({
                "worry_count": profile.worry_count,
                "points": profile.points,
            })

    return render(request, 'worries/hof_list.html', context)


"""
    [명예의 전당 진입 함수]
    - 기능 : 공감 수가 가장 많은 후일담 카드 조회
    - 받는 값 : Epilogue
    - return : hall_of_fame_card 함수로 이동
"""

def hall_of_fame_entry(request):

    top_epilogue = Epilogue.objects.filter(
        worry__is_HoF=True
    ).order_by('-ep_gonggam_count').first()

    if not top_epilogue:
        return redirect("worries:hall_of_fame")

    return redirect("worries:hall_of_fame_card", top_epilogue.id)


"""
    [명예의 전당 - 메인 & 일반 카드 함수]
    - 기능 : 명예의 전당에 공개된 고민, 답변, 후일담 카드로 조회
    - 받는 값 : Worry, Answer, Epilogue
    - return : hof_card.html 화면 표시 
    * 유의사항 : 배우지 않은 문법들이 들어있지만 없으면 구현을 하지 못해서 넣었음 *
            + 공감 수 1등 후일담이면 메인 카드
            + 나머지는 일반 카드
            + 좌우 버튼으로 이전 or 다음 카드 이동 가능
            + 마지막 카드 다음은 메인 카드
            + 메인 카드 이전은 마지막 카드
"""

def hall_of_fame_card(request, epilogue_id):
    epilogue = get_object_or_404(Epilogue, pk=epilogue_id)

    worry = epilogue.worry

    answers = Answer.objects.filter(worry=worry)

    all_epilogues = list(
        Epilogue.objects.filter(
            worry__is_HoF=True
        ).order_by('-ep_gonggam_count')
    )

    if epilogue not in all_epilogues:
        return redirect("worries:hall_of_fame")

    current_index = all_epilogues.index(epilogue)

    is_main = (current_index == 0)

    prev_epilogue = all_epilogues[current_index - 1]

    next_epilogue = all_epilogues[(current_index + 1) % len(all_epilogues)]

    context = {
        'worry' : worry,
        'answers' : answers,
        'epilogue' : epilogue,
        'is_main' : is_main,
        'prev_epilogue' : prev_epilogue,
        'next_epilogue' : next_epilogue,
    }

    return render(request, 'worries/hof_card.html', context)


"""
[답변 만족/불만족 함수]
- 기능 : 고민 작성자가 답변에 대해 만족/불만족 평가
- 받는 값 : answer_id, is_satisfied
- return : 평가 완료 -> 내 고민-답변 화면 이동

* 유의사항 *
    + 고민 작성자만 평가 가능
    + 만족 선택 시 is_satisfied = 1
    + 불만족 선택 시 is_satisfied = -1
    + 답변이 5개이고 전부 평가 완료되면 고민 배송 완료 처리
"""

def edit_satisfaction(request, answer_id, is_satisfied):
    if not request.user.is_authenticated:
        return redirect("accounts:login")
    
    answer = get_object_or_404(Answer, pk=answer_id)

    if request.method != "POST":
        return redirect("writers:get_worry_answer", answer.worry.id)

    # 고민 작성자만 답변에 만족/불만족 가능
    if answer.worry.writer != request.user:
        return redirect("main:home")

    # 답변 만족/불만족 처리
    if (is_satisfied > 0): # 만족
        was_satisfied = (answer.is_satisfied == 1)
        answer.is_satisfied = 1
        if not was_satisfied and answer.writer is not None:
            answerer = get_object_or_404(Profile, writer=answer.writer)
            edit_points(answerer, "답변 만족", 1)  # 답변 만족 시 답변자에게 포인트 지급
    else: # 불만족
        answer.is_satisfied = -1

    answer.save()

    # 답변 개수 확인 후 모든 답변 평가 여부 확인
    answer_count = Answer.objects.filter(worry=answer.worry).count()

    answers = Answer.objects.filter(worry=answer.worry)

    all_checked = True

    for a in answers:
        if a.is_satisfied == 0:
            all_checked = False
            
    # 답변 5개 + 전부 평가 완료 시 배송 완료 처리
    if answer_count == 5 and all_checked:
        answer.worry.is_complete = True
        answer.worry.save()

    return redirect("writers:get_worry_answer", answer.worry.id)
