from datetime import datetime, date, timedelta
import calendar
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils import timezone

from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)

from .models import Entry

class LockedView(LoginRequiredMixin):
    login_url = "admin:login"

class EntryListView(LockedView, ListView):
    model = Entry
    queryset = Entry.objects.all().order_by("-date_created")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get the requested month or use current month
        month_str = self.request.GET.get('month')
        if month_str:
            try:
                current_date = datetime.strptime(month_str + '-01', '%Y-%m-%d')
            except ValueError:
                current_date = timezone.now()
        else:
            current_date = timezone.now()
        
        # Calculate previous and next month
        first_day = current_date.replace(day=1)
        prev_month = (first_day - timedelta(days=1)).replace(day=1)
        next_month = (first_day + timedelta(days=32)).replace(day=1)
        
        # Get calendar for current month
        cal = calendar.monthcalendar(current_date.year, current_date.month)
        
        # Get all entries for the current month
        month_entries = Entry.objects.filter(
            date_created__year=current_date.year,
            date_created__month=current_date.month
        ).values('id', 'title', 'date_created__date')
        
        # Create a dict of dates with entries
        entry_dates = {
            entry['date_created__date']: {
                'id': entry['id'],
                'title': entry['title']
            }
            for entry in month_entries
        }
        
        # Format calendar days with entry information
        calendar_days = []
        today = date.today()
        
        for week in cal:
            week_days = []
            for day in week:
                if day != 0:
                    current_date_day = date(current_date.year, current_date.month, day)
                    day_data = {
                        'date': current_date_day,
                        'is_today': current_date_day == today,
                        'has_entry': current_date_day in entry_dates,
                        'entry': entry_dates.get(current_date_day)
                    }
                    week_days.append(day_data)
                else:
                    week_days.append({'date': None})
            calendar_days.append(week_days)
        
        context.update({
            'calendar_days': calendar_days,
            'current_date': current_date,
            'prev_month': prev_month,
            'next_month': next_month,
        })
        
        return context

class EntryDetailView(LockedView, DetailView):
    model = Entry

class EntryCreateView(LockedView, SuccessMessageMixin, CreateView):
    model = Entry
    fields = ["title", "content"]
    success_url = reverse_lazy("entry-list")
    success_message = "Your new entry was created!"

    def get_initial(self):
        initial = super().get_initial()
        date_str = self.request.GET.get('date')
        if date_str:
            try:
                entry_date = datetime.strptime(date_str, '%Y-%m-%d')
                initial['title'] = f"Entry for {entry_date.strftime('%Y-%m-%d')}"
            except ValueError:
                pass
        return initial

class EntryUpdateView(LockedView, SuccessMessageMixin, UpdateView):
    model = Entry
    fields = ["title", "content"]
    success_message = "Your entry was updated!"

    def get_success_url(self):
        return reverse_lazy(
            "entry-detail",
            kwargs={"pk": self.object.pk}
        )

class EntryDeleteView(LockedView, SuccessMessageMixin, DeleteView):
    model = Entry
    success_url = reverse_lazy("entry-list")
    success_message = "Your entry was deleted!"

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)

