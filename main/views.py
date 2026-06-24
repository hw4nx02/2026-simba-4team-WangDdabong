from django.shortcuts import render, redirect, get_object_or_404
from accounts.models import Profile, UserYang, Attendance
from writers.models import PointLog, Epilogue
from worries.models import Worry, Answer
from .utils import *
from django.utils import timezone
from datetime import timedelta
import random

"""
[홈 화면]
- 기능: 홈 화면 렌더링
- 받는 값 : source
- return: 성공 -> home 렌더링
"""
def home(request, source="DONT_CARE", epilogue_id=None):
    if not request.user.is_authenticated:
        return redirect("accounts:login")
    
    today = timezone.now().date()
    profile = get_object_or_404(Profile, writer=request.user)

    # 출석 체크 가능 여부 검사
    current_week_start = today - timedelta(days=today.weekday())  # 이번 주 월요일 날짜
    current_week_end = current_week_start + timedelta(days=6)    # 이번 주 일요일 날짜

    weekly_attendance = Attendance.objects.filter( # 이번 주 출석 기록
        writer=request.user,
        date__range=(current_week_start, current_week_end)
    )

    weekly_attendance_weekdays = []
    for attendance in weekly_attendance:
        weekly_attendance_weekdays.append(attendance.date.weekday() + 1)

    today_day = today.weekday() + 1
    show_attendance_popup = today_day not in weekly_attendance_weekdays # 오늘 요일이 이번 주 출석 기록에 없으면 팝업 출력

    # 상단 남은 고민 개수, 남은 포인트
    worry_count = profile.worry_count
    points = profile.points

    # 최신 고민 5개 추출
    latest_worries = Worry.objects.filter(
        is_delete = False
    ).order_by("-pub_date")[:5]

    now_worries = []
    for worry in latest_worries:
        try:
            writer_profile = worry.writer.profile
        except Profile.DoesNotExist:
            writer_profile = None

        writer_yang = Yang.get(
            writer_profile.current_yang if writer_profile else "new_yang",
            Yang["new_yang"]
        )
        now_worries.append({
            "worry": worry,
            "yang_image": writer_yang["image"],
            "yang_name": writer_yang["name"],
            "cheerup_count": worry.cheerup_count,
            "answer_count": Answer.objects.filter(worry=worry).count(),
        })

    # 오늘의 멘트 선정
    today_message = random.choice(TODAY_MESSAGES)

    # 후일담 작성 화면에서 왔다면 팝업 출력
    # 기본값
    show_epilogue_popup = False
    epilogue_han_madi = None
    popup_epilogue_id = None

    session_epilogue_id = request.session.pop("show_epilogue_popup_id", None)

    if (
        source == "post_epilogue"
        and epilogue_id is not None
        and session_epilogue_id == epilogue_id
    ):
        epilogue = get_object_or_404(Epilogue, pk=epilogue_id, ep_is_delete=False)
        
        show_epilogue_popup = True
        epilogue_han_madi = epilogue.ep_han_madi
        popup_epilogue_id = epilogue.id

    context = {
        "worry_count": worry_count,
        "points": points,
        "now_worries": now_worries,
        "today_message": today_message,

        "show_epilogue_popup": show_epilogue_popup,
        "epilogue_han_madi": epilogue_han_madi,
        "popup_epilogue_id": popup_epilogue_id,

        "show_attendance_popup": show_attendance_popup,
        "today_day": today_day,
        "attendance_weekdays": weekly_attendance_weekdays
    
    }

    return render(request, 'main/home.html', context)

"""
    [후일담 작성 후 홈 화면으로 전환]
    - 기능: 후일담 작성 후 해당 함수로 진입. 홈 화면으로 전환
"""
def home_from_post_epilogue(request, epilogue_id):
    return home(request, source="post_epilogue", epilogue_id=epilogue_id)

"""
[출석 체크]
- 기능: 출석체크 기능. 포인트 증감 함수 이용
- 받는 값: X
- return: 성공 시 -> 홈 화면 리다이렉트
"""
def daily_attend(request):
    if not request.user.is_authenticated:
        return redirect("accounts:login")

    if request.method != "POST":
        return redirect("main:home")

    profile = get_object_or_404(Profile, writer=request.user)
    today = timezone.now().date()

    current_week_start = today - timedelta(days=today.weekday())  # 이번 주 월요일 날짜
    current_week_end = current_week_start + timedelta(days=6)    # 이번 주 일요일 날짜

    # 오늘 출석 여부 검사
    today_attendance = Attendance.objects.filter(
        writer=request.user,
        date=today
    )
    if today_attendance.exists():
        return redirect("main:home")

    new_attendance = Attendance()   # 오늘 출석 안 했으면 출석 기록 생성
    new_attendance.writer = request.user
    new_attendance.date = today
    new_attendance.save()

    # 기본 출석
    edit_points(profile, "출석", 1)
    profile.last_attendance = today

    # 보너스 점수 검사 (일주일 모두 출석)
    weekly_attendance_count = Attendance.objects.filter(
        writer=request.user,
        date__range=(current_week_start, current_week_end)
    ).count()

    if weekly_attendance_count == 7:    # 일주일 모두 출석
        edit_points(profile, "일주일 출석 보너스", 3)                      # 보너스(3) + 출석(1) = 4

    # 마지막 출석 정보 최신화
    profile.last_attendance = today
    profile.attendance_count = weekly_attendance_count
    profile.save()

    return redirect("main:home")

"""
    [양 성장 과정 구매 화면 렌더링]
    - 기능: 양 성장 과정 구매 화면을 출력
    - 받는 값: X
    - return: 성공 시 -> main/yang_store.html / 실패 시 -> 로그인 화면
"""
def get_store(request):
    if not request.user.is_authenticated:
        return redirect("accounts:login")

    profile = get_object_or_404(Profile, writer=request.user)

    if request.method == "POST":
        source = "고민 구매"
        success = edit_points(profile, source, -5)  # 고민 구매 시 포인트 차감
        
        if success:
            profile.worry_count += 1
            profile.save()
        else:
            request.session["store_popup_message"] = "포인트가 부족해서 구매할 수 없어요."
            
        return redirect("main:get_store")

    yang_items = []

    for yang_id in Yang:
        yang = Yang[yang_id]

        is_owned = UserYang.objects.filter(
            writer=request.user,
            yang_id=yang_id
        ).exists()

        yang_items.append({
            "id": yang_id,
            "name": yang["name"],
            "price": yang["price"],
            "image": yang["image"],
            "description": yang["description"],
            "is_owned": is_owned,
        })

    context = {
        "profile": profile,
        "worry_count": profile.worry_count,
        "points": profile.points,
        "yangs": yang_items,
        "store_popup_message": request.session.pop("store_popup_message", None),
    }

    return render(request, "main/demo_yang_store.html", context)

"""
    [양 성장 과정 구매 함수]
    - 기능: 양 성장 과정 구매 처리
    - 받는 값: 어떤 양 구매할 지(yang_id)
"""
def post_buy_yang(request, yang_id):
    if not request.user.is_authenticated:
        return redirect("accounts:login")

    if UserYang.objects.filter(writer=request.user, yang_id=yang_id).exists():
        return redirect("main:get_store")

    profile = get_object_or_404(Profile, writer=request.user)

    yang = Yang.get(yang_id)
    if yang is None:
        return redirect("main:get_store")

    source = yang["name"] + "구매"
    success = edit_points(profile, source, -yang["price"])
    
    if not success:
        request.session["store_popup_message"] = "포인트가 부족해서 구매할 수 없어요."
        return redirect("main:get_store")

    user_yang = UserYang()
    user_yang.writer = profile.writer
    user_yang.yang_id = yang_id
    user_yang.save()

    return redirect("writers:mypage")

"""
    [후일담 팝업 처리]
    - 기능: 후일담 보러가기 클릭 시
                공개 O -> 명예의 전당 일반 카드 화면 전환
                공개 X -> 고민-답변-후일담 화면 전환
"""
def go_epilogue(request, epilogue_id):
    if not request.user.is_authenticated:
        return redirect("accounts:login")

    epilogue = get_object_or_404(Epilogue, pk=epilogue_id, ep_is_delete=False)

    worry = epilogue.worry

    if worry.is_HoF:    # 공개 O -> 명예의 전당 일반 카드 화면 전환
        return redirect("worries:hall_of_fame_card", epilogue_id)

    return redirect("writers:worry_story", worry_id=worry.id)
