import sqlite3
import datetime


class Database:
    def __init__(self):
        self.conn = sqlite3.connect('Schedules.db')
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def setup_schema(self):
        self.cursor.execute('drop table if exists schedules')
        self.cursor.execute('drop table if exists lessons')
        self.cursor.execute('drop table if exists homeworks')
        self.conn.commit()

        self.cursor.execute('''create table if not exists schedules 
                                (
                                    id integer 
                                        constraint schedules_pk 
                                            primary key autoincrement, 
                                    name text
                                )''')

        self.cursor.execute('''create table if not exists lessons
                                (
                                    id integer
                                        constraint lessons_pk
                                            primary key autoincrement,
                                    name text,
                                    day integer,
                                    time_start datetime,
                                    time_end datetime,
                                    schedule_id int not null
                                        constraint lessons_schedules_id_fk
                                            references schedules
                                                on update cascade on delete cascade
                                )''')

        self.cursor.execute('''create table if not exists homeworks
                                (
                                    id integer
                                        constraint homeworks_pk
                                            primary key autoincrement,
                                    lesson_id integer not null
                                        constraint homeworks_lessons_id_fk
                                            references lessons
                                                on update cascade on delete cascade,
                                    desc text,
                                    week_num integer not null,
                                    year integer not null,
                                    notified integer default 0 not null,
                                    done integer default 0 not null
                                )''')
        self.conn.commit()

        if not self.table_exists('settings'):
            self.cursor.execute('''create table if not exists settings
                                        (
                                            id integer
                                                constraint settings_pk
                                                    primary key autoincrement,
                                            name text not null,
                                            description text,
                                            val text
                                        )''')
            self.cursor.execute('''create unique index settings_name_uindex
                                        on settings (name)''')
        self.conn.commit()

    def table_exists(self, name):
        q = 'select count(*) as cnt from sqlite_master where type = "table" and name = ?'
        v = [name]
        res = self.cursor.execute(q, v).fetchone()
        return dict(res)['cnt'] == 1

    '''
    SETTINGS
    '''
    def add_setting(self, **kwargs):
        f = ['name']
        v = [kwargs['name']]
        if 'desc' in kwargs:
            f.append('description')
            v.append(kwargs['description'])
        if 'val' in kwargs:
            f.append('val')
            v.append(kwargs['val'])
        v.append(kwargs['name'])
        q = 'insert into settings (' + ','.join(f) + ''')
                    select ''' + ','.join(['?'] * len(f)) + '''
                    where not exists(select 1 from settings where name = ?)'''
        self.cursor.execute(q, v)
        self.conn.commit()

    def get_setting(self, name):

        q = 'select * from settings where name = ?'
        self.cursor.execute(q, [name])
        rows = [dict(row) for row in self.cursor.fetchall()]
        cnt = len(rows)
        if cnt == 0:
            return None
        else:
            return rows[0]['val']

    def update_setting(self, name, val):
        v = [val, name]
        self.cursor.execute('update settings set val = ? where name = ?', v)
        self.conn.commit()

    '''
    SCHEDULE
    '''
    def get_schedules(self, **kwargs):
        w = []
        v = []
        q = 'select s.* from schedules s'
        if 'day' in kwargs:
            w.append('exists(select * from lessons l where l.schedule_id = s.id and l.day = ?)')
            v.append(kwargs['day'])

        if len(w) > 0:
            q += ' where ' + ' and '.join(w)
        self.cursor.execute(q, v)
        return [dict(row) for row in self.cursor.fetchall()]

    def get_schedule(self, schedule_id):
        self.cursor.execute('select * from schedules where id = ?', [schedule_id])
        return dict(self.cursor.fetchone())

    def add_schedule(self, **kwargs):
        values = [kwargs['name']]
        schedule_id = self.cursor.execute('insert into schedules (name) values (?)', values)
        self.conn.commit()
        return schedule_id.lastrowid

    def update_schedule(self, **kwargs):
        values = [kwargs['name'], kwargs['id']]
        self.cursor.execute('update schedules set name = ? where id = ?', values)
        self.conn.commit()

    def delete_schedule(self, schedule_id):
        self.cursor.execute('delete from schedules where id = ?', [schedule_id])
        self.conn.commit()

    '''
    LESSON
    '''
    def get_lessons(self, **kwargs):
        w = []
        v = []
        q = 'select l.*, h.desc as homework_desc from lessons l left join homeworks h on l.id = h.lesson_id'
        if 'homework_week_num' in kwargs and 'homework_year' in kwargs:
            q += ' and h.week_num = ? and year = ?'
            v.append(kwargs['homework_week_num'])
            v.append(kwargs['homework_year'])
        if 'schedule_id' in kwargs:
            w.append('l.schedule_id = ?')
            v.append(kwargs['schedule_id'])
        if 'day' in kwargs:
            w.append('l.day = ?')
            v.append(kwargs['day'])
        if len(w) > 0:
            q += ' where ' + ' and '.join(w)
        q += ' order by l.day, (case when l.time_start = "" then 1 else 0 end), l.time_start'
        self.cursor.execute(q, v)
        return [dict(row) for row in self.cursor.fetchall()]

    def get_lesson(self, **kwargs):
        w = []
        v = []
        if 'id' in kwargs:
            w.append('id = ?')
            v.append(kwargs['id'])
        if 'schedule_id' in kwargs:
            w.append('schedule_id = ?')
            v.append(kwargs['schedule_id'])
        q = 'select * from lessons'
        if len(w) > 0:
            q += ' where ' + ' and '.join(w)

        self.cursor.execute(q, v)
        return dict(self.cursor.fetchone())

    def update_lesson(self, **kwargs):
        f = []
        v = []
        if 'name' in kwargs:
            f.append('name = ?')
            v.append(kwargs['name'])
        if 'time_start' in kwargs:
            f.append('time_start = ?')
            v.append(kwargs['time_start'])
        if 'time_end' in kwargs:
            f.append('time_end = ?')
            v.append(kwargs['time_end'])
        v.append(kwargs['id'])
        self.cursor.execute('update lessons set ' + ','.join(f) + ' where id = ?', v)
        self.conn.commit()

    def add_lessons(self, lessons):
        values = []
        for lesson in lessons:
            values.append((lesson['name'], lesson['day'], lesson['time_start'], lesson['time_end'], lesson['schedule_id']))
        self.cursor.executemany('insert into lessons (name, day, time_start, time_end, schedule_id) values (?,?,?,?,?)', values)
        self.conn.commit()

    def delete_lessons(self, **kwargs):
        w = []
        v = []
        q = '''delete from lessons'''
        if 'schedule_id' in kwargs:
            w.append('schedule_id = ?')
            v.append(kwargs['schedule_id'])
        if 'id' in kwargs:
            w.append('id = ?')
            v.append(kwargs['id'])
        if len(w) > 0:
            q += ' where ' + ' and '.join(w)
        self.cursor.execute(q, v)
        self.conn.commit()

    '''
    HOMEWORK
    '''
    def get_homework(self, homework_id):
        self.cursor.execute('''select h.*, l.schedule_id, l.id as lesson_id from homeworks h
                                    join lessons l on h.lesson_id = l.id
                                where h.id = ?''', [homework_id])
        return dict(self.cursor.fetchone())

    def get_homeworks(self, **kwargs):
        w = []
        v = []
        q = '''select h.id, h.desc, s.name as schedule_name, l.name as lesson_name from homeworks h
                            join lessons l on l.id = h.lesson_id
                            join schedules s on s.id = l.schedule_id'''
        if 'year' in kwargs:
            w.append('h.year = ?')
            v.append(kwargs['year'])
        if 'week_num' in kwargs:
            w.append('h.week_num = ?')
            v.append(kwargs['week_num'])
        if 'day' in kwargs:
            w.append('l.day = ?')
            v.append(kwargs['day'])
        if 'notified' in kwargs:
            w.append('h.notified = ?')
            v.append(kwargs['notified'])
        if 'done' in kwargs:
            w.append('h.done = ?')
            v.append(kwargs['done'])
        if len(w) > 0:
            q += ' where ' + ' and '.join(w)
        self.cursor.execute(q, v)
        return [dict(row) for row in self.cursor.fetchall()]

    def find_homework(self, **kwargs):
        w = []
        v = []
        q = 'select * from homeworks where lesson_id = ? and year = ? and week_num = ?'
        v.append(kwargs['lesson_id'])
        v.append(kwargs['year'])
        v.append(kwargs['week_num'])
        if len(w) > 0:
            q += ' where ' + ' and '.join(w)
        self.cursor.execute(q, v)
        rows = [dict(row) for row in self.cursor.fetchall()]
        cnt = len(rows)
        if cnt == 0:
            return None
        elif cnt > 1:
            return False
        else:
            return rows[0]

    def homework_exists(self, **kwargs):
        q = 'select count(*) as cnt from homeworks'
        w = []
        v = []
        if 'lesson_id' in kwargs:
            w.append('lesson_id = ?')
            v.append(kwargs['lesson_id'])
        if 'week_num' in kwargs:
            w.append('week_num = ?')
            v.append(kwargs['week_num'])
        if 'year' in kwargs:
            w.append('year = ?')
            v.append(kwargs['year'])
        if len(w) > 0:
            q += ' where ' + ' and '.join(w)
        res = self.cursor.execute(q, v).fetchone()
        return dict(res)['cnt'] > 0

    def add_homework(self, **kwargs):
        f = ['lesson_id', 'desc', 'week_num', 'year']
        v = [kwargs['lesson_id'], kwargs['desc'], kwargs['week_num'], kwargs['year']]
        if 'notified' in kwargs:
            f.append('notified')
            v.append(kwargs['notified'])
        if 'done' in kwargs:
            f.append('done')
            v.append(kwargs['done'])
        self.cursor.execute('insert into homeworks (' + ','.join(f) + ') values (' + ','.join(['?'] * len(f)) + ')', tuple(v))
        self.conn.commit()

    def schedule_has_homeworks(self, **kwargs):
        q = '''select count(*) as cnt from homeworks h
                    join lessons l on h.lesson_id = l.id
                    join schedules s on s.id = l.schedule_id'''
        w = ['s.id = ?']
        v = [kwargs['schedule_id']]
        if 'year' in kwargs and 'week_num' in kwargs:
            w.append('((h.year = ? and h.week_num >= ?) or h.year > ?)')
            v.append(kwargs['year'])
            v.append(kwargs['week_num'])
            v.append(kwargs['year'])

        if len(w) > 0:
            q += ' where ' + ' and '.join(w)
        res = self.cursor.execute(q, v).fetchone()
        return dict(res)['cnt'] > 0

    def lesson_has_homeworks(self, **kwargs):
        q = 'select count(*) as cnt from homeworks'
        w = ['lesson_id = ?']
        v = [kwargs['lesson_id']]
        if 'year' in kwargs and 'week_num' in kwargs:
            w.append('((year = ? and week_num >= ?) or year > ?)')
            v.append(kwargs['year'])
            v.append(kwargs['week_num'])
            v.append(kwargs['year'])

        if len(w) > 0:
            q += ' where ' + ' and '.join(w)
        res = self.cursor.execute(q, v).fetchone()
        return dict(res)['cnt'] > 0

    def delete_homeworks(self, **kwargs):
        w = None
        v = []
        if 'schedule_id' in kwargs:
            w = 'l.schedule_id'
            v.append(kwargs['schedule_id'])
        elif 'lesson_id' in kwargs:
            w = 'l.id'
            v.append(kwargs['lesson_id'])
        q = '''delete from homeworks where id in (select h.id from homeworks h
                                        join lessons l on h.lesson_id = l.id'''
        if w is not None:
            q += f' where {w} = ?)'
        else:
            q += ')'

        self.cursor.execute(q, v)
        self.conn.commit()

    def delete_homework(self, homework_id):
        self.cursor.execute('delete from homeworks where id = ?', [homework_id])
        self.conn.commit()

    def update_homework(self, **kwargs):
        f = []
        v = []
        if 'desc' in kwargs:
            f.append('desc = ?')
            v.append(kwargs['desc'])
        if 'done' in kwargs:
            f.append('done = ?')
            v.append(kwargs['done'])
        if 'notified' in kwargs:
            f.append('notified = ?')
            v.append(kwargs['notified'])
        v.append(kwargs['id'])
        self.cursor.execute('update homeworks set ' + ','.join(f) + ' where id = ?', v)
        self.conn.commit()

    def get_upcoming_homeworks(self, **kwargs):
        q = '''select h.*, s.id as schedule_id, s.name as schedule_name, l.day, l.name as lesson_name, l.time_start as lesson_time_start 
                from homeworks h
                    join lessons l on h.lesson_id = l.id
                    join schedules s on l.schedule_id = s.id
                where (h.week_num >= ? and h.year = ? and l.day >= ?) or h.year > ?
                order by h.year, h.week_num, l.day, (case when l.time_start = "" then 1 else 0 end), l.time_start'''
        v = [kwargs['week_num'], kwargs['year'], kwargs['day'], kwargs['year']]
        self.cursor.execute(q, v)
        return [dict(row) for row in self.cursor.fetchall()]
