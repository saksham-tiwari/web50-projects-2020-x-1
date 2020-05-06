create table books(
	id serial primary key,
	isbn varchar not null,
	title varchar not null,
	author varchar not null,
	year integer not null
);
create table users(
	id serial primary key,
	username varchar not null,
	password varchar not null,
	email varchar unique not null
);
create table reviews(
	id serial primary key,
    user_id integer references users,
    book_id integer references books,
    rating integer not null constraint Invalid_Rating check (rating <=5 AND rating>=1),
    comment text,
    date text 
); 