'use client'

import React from 'react'
import { format, startOfMonth, endOfMonth, eachDayOfInterval, isSameMonth, isSameDay, isToday, addMonths, subMonths } from 'date-fns'

interface CalendarEvent {
  id: number
  date: string
  time?: string
  title: string
  type: string
  color?: string
}

interface CalendarProps {
  events: CalendarEvent[]
  onDateClick?: (date: Date) => void
  onEventClick?: (event: CalendarEvent) => void
}

export default function Calendar({ events, onDateClick, onEventClick }: CalendarProps) {
  const [currentMonth, setCurrentMonth] = React.useState(new Date())

  const monthStart = startOfMonth(currentMonth)
  const monthEnd = endOfMonth(currentMonth)
  const daysInMonth = eachDayOfInterval({ start: monthStart, end: monthEnd })

  // Adicionar dias do início da semana anterior
  const startDay = monthStart.getDay()
  const daysBeforeMonth: Date[] = []
  for (let i = startDay - 1; i >= 0; i--) {
    daysBeforeMonth.push(new Date(monthStart.getFullYear(), monthStart.getMonth(), monthStart.getDate() - i - 1))
  }

  const allDays = [...daysBeforeMonth, ...daysInMonth]

  const getEventsForDate = (date: Date) => {
    return events.filter(event => {
      const eventDate = new Date(event.date)
      return isSameDay(eventDate, date)
    })
  }

  const getEventColor = (type: string) => {
    const colors: Record<string, string> = {
      task: 'bg-blue-500',
      call: 'bg-green-500',
      meeting: 'bg-purple-500',
      note: 'bg-gray-500'
    }
    return colors[type] || 'bg-gray-500'
  }

  const nextMonth = () => setCurrentMonth(addMonths(currentMonth, 1))
  const prevMonth = () => setCurrentMonth(subMonths(currentMonth, 1))

  return (
    <div className="bg-slate-900 border border-white/10 rounded-lg shadow p-6">
      {/* Header do Calendário */}
      <div className="flex items-center justify-between mb-6">
        <button
          onClick={prevMonth}
          className="p-2 hover:bg-white/5 rounded-md transition-colors text-slate-400 hover:text-white"
          aria-label="Mês anterior"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <h3 className="text-xl font-semibold text-white">
          {format(currentMonth, 'MMMM yyyy')}
        </h3>
        <button
          onClick={nextMonth}
          className="p-2 hover:bg-white/5 rounded-md transition-colors text-slate-400 hover:text-white"
          aria-label="Próximo mês"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>

      {/* Dias da semana */}
      <div className="grid grid-cols-7 gap-1 mb-2">
        {['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'].map((day) => (
          <div key={day} className="text-center text-sm font-medium text-slate-500 py-2">
            {day}
          </div>
        ))}
      </div>

      {/* Grid do calendário */}
      <div className="grid grid-cols-7 gap-1">
        {allDays.map((day, idx) => {
          const dayEvents = getEventsForDate(day)
          const isCurrentMonth = isSameMonth(day, currentMonth)
          const isCurrentDay = isToday(day)

          return (
            <div
              key={idx}
              onClick={() => onDateClick && onDateClick(day)}
              className={`min-h-[100px] p-2 border border-white/10 rounded-md cursor-pointer transition-all hover:bg-white/5 ${!isCurrentMonth ? 'opacity-30' : ''
                } ${isCurrentDay ? 'bg-blue-900/20 border-blue-500/30' : ''}`}
            >
              <div className={`text-sm font-medium mb-1 ${isCurrentDay ? 'text-blue-400' : 'text-slate-300'}`}>
                {format(day, 'd')}
              </div>
              <div className="space-y-1">
                {dayEvents.slice(0, 3).map((event) => (
                  <div
                    key={event.id}
                    onClick={(e) => {
                      e.stopPropagation()
                      onEventClick && onEventClick(event)
                    }}
                    className={`text-xs p-1 rounded ${getEventColor(event.type)} text-white truncate cursor-pointer hover:opacity-80`}
                    title={event.title}
                  >
                    {event.time && `${event.time} - `}
                    {event.title}
                  </div>
                ))}
                {dayEvents.length > 3 && (
                  <div className="text-xs text-slate-500">
                    +{dayEvents.length - 3} mais
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

