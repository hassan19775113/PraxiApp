-- Generated from infrastructure/docs/public_schema.json
-- Note: CHECK/constraint definitions may not be fully represented in the JSON export.
BEGIN;

CREATE TABLE IF NOT EXISTS public.appointments_appointment (
  id integer NOT NULL,
  patient_id integer NOT NULL,
  start_time timestamptz NOT NULL,
  end_time timestamptz NOT NULL,
  status varchar(20) NOT NULL,
  notes text,
  created_at timestamptz NOT NULL,
  updated_at timestamptz NOT NULL,
  doctor_id bigint NOT NULL,
  type_id bigint
);

CREATE TABLE IF NOT EXISTS public.appointments_appointmentresource (
  id bigint NOT NULL,
  appointment_id integer NOT NULL,
  resource_id bigint NOT NULL
);

CREATE TABLE IF NOT EXISTS public.appointments_appointmenttype (
  id bigint NOT NULL,
  name varchar(100) NOT NULL,
  color varchar(7),
  duration_minutes integer,
  active boolean NOT NULL,
  created_at timestamptz NOT NULL,
  updated_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS public.appointments_doctorabsence (
  id bigint NOT NULL,
  start_date date NOT NULL,
  end_date date NOT NULL,
  reason varchar(255),
  active boolean NOT NULL,
  created_at timestamptz NOT NULL,
  updated_at timestamptz NOT NULL,
  doctor_id bigint NOT NULL,
  duration_workdays integer,
  remaining_days integer,
  return_date date
);

CREATE TABLE IF NOT EXISTS public.appointments_doctorbreak (
  id bigint NOT NULL,
  date date NOT NULL,
  start_time time NOT NULL,
  end_time time NOT NULL,
  reason varchar(255),
  active boolean NOT NULL,
  created_at timestamptz NOT NULL,
  updated_at timestamptz NOT NULL,
  doctor_id bigint
);

CREATE TABLE IF NOT EXISTS public.appointments_doctorhours (
  id bigint NOT NULL,
  weekday integer NOT NULL,
  start_time time NOT NULL,
  end_time time NOT NULL,
  active boolean NOT NULL,
  created_at timestamptz NOT NULL,
  updated_at timestamptz NOT NULL,
  doctor_id bigint NOT NULL
);

CREATE TABLE IF NOT EXISTS public.appointments_operation (
  id bigint NOT NULL,
  patient_id integer NOT NULL,
  start_time timestamptz NOT NULL,
  end_time timestamptz NOT NULL,
  status varchar(20) NOT NULL,
  notes text,
  created_at timestamptz NOT NULL,
  updated_at timestamptz NOT NULL,
  anesthesist_id bigint,
  assistant_id bigint,
  op_room_id bigint NOT NULL,
  op_type_id bigint NOT NULL,
  primary_surgeon_id bigint NOT NULL
);

CREATE TABLE IF NOT EXISTS public.appointments_operationdevice (
  id bigint NOT NULL,
  operation_id bigint NOT NULL,
  resource_id bigint NOT NULL
);

CREATE TABLE IF NOT EXISTS public.appointments_operationtype (
  id bigint NOT NULL,
  name varchar(255) NOT NULL,
  prep_duration integer NOT NULL,
  op_duration integer NOT NULL,
  post_duration integer NOT NULL,
  color varchar(7) NOT NULL,
  active boolean NOT NULL,
  created_at timestamptz NOT NULL,
  updated_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS public.appointments_patientflow (
  id bigint NOT NULL,
  status varchar(32) NOT NULL,
  arrival_time timestamptz,
  status_changed_at timestamptz NOT NULL,
  notes text,
  appointment_id integer,
  operation_id bigint
);

CREATE TABLE IF NOT EXISTS public.appointments_practicehours (
  id bigint NOT NULL,
  weekday integer NOT NULL,
  start_time time NOT NULL,
  end_time time NOT NULL,
  active boolean NOT NULL,
  created_at timestamptz NOT NULL,
  updated_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS public.appointments_resource (
  id bigint NOT NULL,
  name varchar(255) NOT NULL,
  type varchar(20) NOT NULL,
  color varchar(7) NOT NULL,
  active boolean NOT NULL,
  created_at timestamptz NOT NULL,
  updated_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS public.auth_group (
  id integer NOT NULL,
  name varchar(150) NOT NULL
);

CREATE TABLE IF NOT EXISTS public.auth_group_permissions (
  id bigint NOT NULL,
  group_id integer NOT NULL,
  permission_id integer NOT NULL
);

CREATE TABLE IF NOT EXISTS public.auth_permission (
  id integer NOT NULL,
  name varchar(255) NOT NULL,
  content_type_id integer NOT NULL,
  codename varchar(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS public.core_auditlog (
  id bigint NOT NULL,
  role_name varchar(50) NOT NULL,
  action varchar(50) NOT NULL,
  patient_id integer,
  timestamp timestamptz NOT NULL,
  meta jsonb,
  user_id bigint
);

CREATE TABLE IF NOT EXISTS public.core_role (
  id bigint NOT NULL,
  name varchar(64) NOT NULL,
  label varchar(128) NOT NULL
);

CREATE TABLE IF NOT EXISTS public.core_user (
  id bigint NOT NULL,
  password varchar(128) NOT NULL,
  last_login timestamptz,
  is_superuser boolean NOT NULL,
  username varchar(150) NOT NULL,
  first_name varchar(150) NOT NULL,
  last_name varchar(150) NOT NULL,
  is_staff boolean NOT NULL,
  is_active boolean NOT NULL,
  date_joined timestamptz NOT NULL,
  email varchar(254) NOT NULL,
  role_id bigint,
  calendar_color varchar(7) NOT NULL,
  vacation_days_per_year integer NOT NULL
);

CREATE TABLE IF NOT EXISTS public.core_user_groups (
  id bigint NOT NULL,
  user_id bigint NOT NULL,
  group_id integer NOT NULL
);

CREATE TABLE IF NOT EXISTS public.core_user_user_permissions (
  id bigint NOT NULL,
  user_id bigint NOT NULL,
  permission_id integer NOT NULL
);

CREATE TABLE IF NOT EXISTS public.django_admin_log (
  id integer NOT NULL,
  action_time timestamptz NOT NULL,
  object_id text,
  object_repr varchar(200) NOT NULL,
  action_flag smallint NOT NULL,
  change_message text NOT NULL,
  content_type_id integer,
  user_id bigint NOT NULL
);

CREATE TABLE IF NOT EXISTS public.django_content_type (
  id integer NOT NULL,
  app_label varchar(100) NOT NULL,
  model varchar(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS public.django_migrations (
  id bigint NOT NULL,
  app varchar(255) NOT NULL,
  name varchar(255) NOT NULL,
  applied timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS public.django_session (
  session_key varchar(40) NOT NULL,
  session_data text NOT NULL,
  expire_date timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS public.patient_documents (
  id bigint NOT NULL,
  patient_id integer NOT NULL,
  title varchar(255) NOT NULL,
  doc_type varchar(20) NOT NULL,
  file varchar(100),
  note text NOT NULL,
  created_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS public.patient_notes (
  id bigint NOT NULL,
  patient_id integer NOT NULL,
  author_name varchar(255) NOT NULL,
  content text NOT NULL,
  created_at timestamptz NOT NULL,
  author_role varchar(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS public.patients (
  id integer NOT NULL,
  first_name varchar(100) NOT NULL,
  last_name varchar(100) NOT NULL,
  birth_date date,
  gender varchar(20),
  phone varchar(50),
  email varchar(255),
  created_at timestamptz,
  updated_at timestamptz
);

ALTER TABLE public.appointments_appointment ADD CONSTRAINT appointments_appointment_pkey PRIMARY KEY (id);
ALTER TABLE public.appointments_appointmentresource ADD CONSTRAINT appointments_appointmentresource_pkey PRIMARY KEY (id);
ALTER TABLE public.appointments_appointmenttype ADD CONSTRAINT appointments_appointmenttype_pkey PRIMARY KEY (id);
ALTER TABLE public.appointments_doctorabsence ADD CONSTRAINT appointments_doctorabsence_pkey PRIMARY KEY (id);
ALTER TABLE public.appointments_doctorbreak ADD CONSTRAINT appointments_doctorbreak_pkey PRIMARY KEY (id);
ALTER TABLE public.appointments_doctorhours ADD CONSTRAINT appointments_doctorhours_pkey PRIMARY KEY (id);
ALTER TABLE public.appointments_operation ADD CONSTRAINT appointments_operation_pkey PRIMARY KEY (id);
ALTER TABLE public.appointments_operationdevice ADD CONSTRAINT appointments_operationdevice_pkey PRIMARY KEY (id);
ALTER TABLE public.appointments_operationtype ADD CONSTRAINT appointments_operationtype_pkey PRIMARY KEY (id);
ALTER TABLE public.appointments_patientflow ADD CONSTRAINT appointments_patientflow_pkey PRIMARY KEY (id);
ALTER TABLE public.appointments_practicehours ADD CONSTRAINT appointments_practicehours_pkey PRIMARY KEY (id);
ALTER TABLE public.appointments_resource ADD CONSTRAINT appointments_resource_pkey PRIMARY KEY (id);
ALTER TABLE public.auth_group ADD CONSTRAINT auth_group_pkey PRIMARY KEY (id);
ALTER TABLE public.auth_group_permissions ADD CONSTRAINT auth_group_permissions_pkey PRIMARY KEY (id);
ALTER TABLE public.auth_permission ADD CONSTRAINT auth_permission_pkey PRIMARY KEY (id);
ALTER TABLE public.core_auditlog ADD CONSTRAINT core_auditlog_pkey PRIMARY KEY (id);
ALTER TABLE public.core_role ADD CONSTRAINT core_role_pkey PRIMARY KEY (id);
ALTER TABLE public.core_user ADD CONSTRAINT core_user_pkey PRIMARY KEY (id);
ALTER TABLE public.core_user_groups ADD CONSTRAINT core_user_groups_pkey PRIMARY KEY (id);
ALTER TABLE public.core_user_user_permissions ADD CONSTRAINT core_user_user_permissions_pkey PRIMARY KEY (id);
ALTER TABLE public.django_admin_log ADD CONSTRAINT django_admin_log_pkey PRIMARY KEY (id);
ALTER TABLE public.django_content_type ADD CONSTRAINT django_content_type_pkey PRIMARY KEY (id);
ALTER TABLE public.django_migrations ADD CONSTRAINT django_migrations_pkey PRIMARY KEY (id);
ALTER TABLE public.django_session ADD CONSTRAINT django_session_pkey PRIMARY KEY (session_key);
ALTER TABLE public.patient_documents ADD CONSTRAINT patient_documents_pkey PRIMARY KEY (id);
ALTER TABLE public.patient_notes ADD CONSTRAINT patient_notes_pkey PRIMARY KEY (id);
ALTER TABLE public.patients ADD CONSTRAINT patients_pkey PRIMARY KEY (id);

ALTER TABLE public.appointments_appointment ADD CONSTRAINT fk_appointments_appointment_doctor_id FOREIGN KEY (doctor_id) REFERENCES public.core_user (id);
ALTER TABLE public.appointments_appointment ADD CONSTRAINT fk_appointments_appointment_type_id FOREIGN KEY (type_id) REFERENCES public.appointments_appointmenttype (id);
ALTER TABLE public.appointments_appointmentresource ADD CONSTRAINT fk_appointments_appointmentresource_appointment_id FOREIGN KEY (appointment_id) REFERENCES public.appointments_appointment (id);
ALTER TABLE public.appointments_appointmentresource ADD CONSTRAINT fk_appointments_appointmentresource_resource_id FOREIGN KEY (resource_id) REFERENCES public.appointments_resource (id);
ALTER TABLE public.appointments_doctorabsence ADD CONSTRAINT fk_appointments_doctorabsence_doctor_id FOREIGN KEY (doctor_id) REFERENCES public.core_user (id);
ALTER TABLE public.appointments_doctorbreak ADD CONSTRAINT fk_appointments_doctorbreak_doctor_id FOREIGN KEY (doctor_id) REFERENCES public.core_user (id);
ALTER TABLE public.appointments_doctorhours ADD CONSTRAINT fk_appointments_doctorhours_doctor_id FOREIGN KEY (doctor_id) REFERENCES public.core_user (id);
ALTER TABLE public.appointments_operation ADD CONSTRAINT fk_appointments_operation_anesthesist_id FOREIGN KEY (anesthesist_id) REFERENCES public.core_user (id);
ALTER TABLE public.appointments_operation ADD CONSTRAINT fk_appointments_operation_assistant_id FOREIGN KEY (assistant_id) REFERENCES public.core_user (id);
ALTER TABLE public.appointments_operation ADD CONSTRAINT fk_appointments_operation_op_room_id FOREIGN KEY (op_room_id) REFERENCES public.appointments_resource (id);
ALTER TABLE public.appointments_operation ADD CONSTRAINT fk_appointments_operation_op_type_id FOREIGN KEY (op_type_id) REFERENCES public.appointments_operationtype (id);
ALTER TABLE public.appointments_operation ADD CONSTRAINT fk_appointments_operation_primary_surgeon_id FOREIGN KEY (primary_surgeon_id) REFERENCES public.core_user (id);
ALTER TABLE public.appointments_operationdevice ADD CONSTRAINT fk_appointments_operationdevice_operation_id FOREIGN KEY (operation_id) REFERENCES public.appointments_operation (id);
ALTER TABLE public.appointments_operationdevice ADD CONSTRAINT fk_appointments_operationdevice_resource_id FOREIGN KEY (resource_id) REFERENCES public.appointments_resource (id);
ALTER TABLE public.appointments_patientflow ADD CONSTRAINT fk_appointments_patientflow_appointment_id FOREIGN KEY (appointment_id) REFERENCES public.appointments_appointment (id);
ALTER TABLE public.appointments_patientflow ADD CONSTRAINT fk_appointments_patientflow_operation_id FOREIGN KEY (operation_id) REFERENCES public.appointments_operation (id);
ALTER TABLE public.auth_group_permissions ADD CONSTRAINT fk_auth_group_permissions_group_id FOREIGN KEY (group_id) REFERENCES public.auth_group (id);
ALTER TABLE public.auth_group_permissions ADD CONSTRAINT fk_auth_group_permissions_permission_id FOREIGN KEY (permission_id) REFERENCES public.auth_permission (id);
ALTER TABLE public.auth_permission ADD CONSTRAINT fk_auth_permission_content_type_id FOREIGN KEY (content_type_id) REFERENCES public.django_content_type (id);
ALTER TABLE public.core_auditlog ADD CONSTRAINT fk_core_auditlog_user_id FOREIGN KEY (user_id) REFERENCES public.core_user (id);
ALTER TABLE public.core_user ADD CONSTRAINT fk_core_user_role_id FOREIGN KEY (role_id) REFERENCES public.core_role (id);
ALTER TABLE public.core_user_groups ADD CONSTRAINT fk_core_user_groups_group_id FOREIGN KEY (group_id) REFERENCES public.auth_group (id);
ALTER TABLE public.core_user_groups ADD CONSTRAINT fk_core_user_groups_user_id FOREIGN KEY (user_id) REFERENCES public.core_user (id);
ALTER TABLE public.core_user_user_permissions ADD CONSTRAINT fk_core_user_user_permissions_permission_id FOREIGN KEY (permission_id) REFERENCES public.auth_permission (id);
ALTER TABLE public.core_user_user_permissions ADD CONSTRAINT fk_core_user_user_permissions_user_id FOREIGN KEY (user_id) REFERENCES public.core_user (id);
ALTER TABLE public.django_admin_log ADD CONSTRAINT fk_django_admin_log_content_type_id FOREIGN KEY (content_type_id) REFERENCES public.django_content_type (id);
ALTER TABLE public.django_admin_log ADD CONSTRAINT fk_django_admin_log_user_id FOREIGN KEY (user_id) REFERENCES public.core_user (id);
ALTER TABLE public.patient_documents ADD CONSTRAINT fk_patient_documents_patient_id FOREIGN KEY (patient_id) REFERENCES public.patients (id);
ALTER TABLE public.patient_notes ADD CONSTRAINT fk_patient_notes_patient_id FOREIGN KEY (patient_id) REFERENCES public.patients (id);

CREATE INDEX appointments_appointment_doctor_id_fb58c3a1 ON public.appointments_appointment USING btree (doctor_id);
CREATE INDEX appointments_appointment_type_id_0798a0cf ON public.appointments_appointment USING btree (type_id);
CREATE UNIQUE INDEX appointments_appointment_appointment_id_resource__1603c3ed_uniq ON public.appointments_appointmentresource USING btree (appointment_id, resource_id);
CREATE INDEX appointments_appointmentresource_appointment_id_5171072f ON public.appointments_appointmentresource USING btree (appointment_id);
CREATE INDEX appointments_appointmentresource_resource_id_b5b7d8d8 ON public.appointments_appointmentresource USING btree (resource_id);
CREATE INDEX appointments_doctorabsence_doctor_id_381a94fe ON public.appointments_doctorabsence USING btree (doctor_id);
CREATE INDEX appointments_doctorbreak_doctor_id_c4722ccc ON public.appointments_doctorbreak USING btree (doctor_id);
CREATE INDEX appointments_doctorhours_doctor_id_f02a7890 ON public.appointments_doctorhours USING btree (doctor_id);
CREATE UNIQUE INDEX uniq_doctorhours_slot_active ON public.appointments_doctorhours USING btree (doctor_id, weekday, start_time, end_time, active);
CREATE INDEX appointments_operation_anesthesist_id_251861a1 ON public.appointments_operation USING btree (anesthesist_id);
CREATE INDEX appointments_operation_assistant_id_30e38698 ON public.appointments_operation USING btree (assistant_id);
CREATE INDEX appointments_operation_op_room_id_f83c262a ON public.appointments_operation USING btree (op_room_id);
CREATE INDEX appointments_operation_op_type_id_e202b80f ON public.appointments_operation USING btree (op_type_id);
CREATE INDEX appointments_operation_primary_surgeon_id_c50617d2 ON public.appointments_operation USING btree (primary_surgeon_id);
CREATE UNIQUE INDEX appointments_operationde_operation_id_resource_id_9c7f25d2_uniq ON public.appointments_operationdevice USING btree (operation_id, resource_id);
CREATE INDEX appointments_operationdevice_operation_id_53a746e9 ON public.appointments_operationdevice USING btree (operation_id);
CREATE INDEX appointments_operationdevice_resource_id_a8a6c6a8 ON public.appointments_operationdevice USING btree (resource_id);
CREATE INDEX appointments_patientflow_appointment_id_88f43be2 ON public.appointments_patientflow USING btree (appointment_id);
CREATE INDEX appointments_patientflow_operation_id_801a5696 ON public.appointments_patientflow USING btree (operation_id);
CREATE INDEX auth_group_name_a6ea08ec_like ON public.auth_group USING btree (name varchar_pattern_ops);
CREATE UNIQUE INDEX auth_group_name_key ON public.auth_group USING btree (name);
CREATE INDEX auth_group_permissions_group_id_b120cbf9 ON public.auth_group_permissions USING btree (group_id);
CREATE UNIQUE INDEX auth_group_permissions_group_id_permission_id_0cd325b0_uniq ON public.auth_group_permissions USING btree (group_id, permission_id);
CREATE INDEX auth_group_permissions_permission_id_84c5c92e ON public.auth_group_permissions USING btree (permission_id);
CREATE INDEX auth_permission_content_type_id_2f476e4b ON public.auth_permission USING btree (content_type_id);
CREATE UNIQUE INDEX auth_permission_content_type_id_codename_01ab375a_uniq ON public.auth_permission USING btree (content_type_id, codename);
CREATE INDEX core_auditl_action_096de0_idx ON public.core_auditlog USING btree (action, "timestamp");
CREATE INDEX core_auditl_patient_df3a3d_idx ON public.core_auditlog USING btree (patient_id, "timestamp");
CREATE INDEX core_auditlog_action_978477aa ON public.core_auditlog USING btree (action);
CREATE INDEX core_auditlog_action_978477aa_like ON public.core_auditlog USING btree (action varchar_pattern_ops);
CREATE INDEX core_auditlog_patient_id_accdd9bb ON public.core_auditlog USING btree (patient_id);
CREATE INDEX core_auditlog_role_name_261349e8 ON public.core_auditlog USING btree (role_name);
CREATE INDEX core_auditlog_role_name_261349e8_like ON public.core_auditlog USING btree (role_name varchar_pattern_ops);
CREATE INDEX core_auditlog_timestamp_c6ef4463 ON public.core_auditlog USING btree ("timestamp");
CREATE INDEX core_auditlog_user_id_3797aaab ON public.core_auditlog USING btree (user_id);
CREATE INDEX core_role_name_ca4cd9c7_like ON public.core_role USING btree (name varchar_pattern_ops);
CREATE UNIQUE INDEX core_role_name_key ON public.core_role USING btree (name);
CREATE INDEX core_user_email_92a71487_like ON public.core_user USING btree (email varchar_pattern_ops);
CREATE UNIQUE INDEX core_user_email_key ON public.core_user USING btree (email);
CREATE INDEX core_user_role_id_8de62872 ON public.core_user USING btree (role_id);
CREATE INDEX core_user_username_36e4f7f7_like ON public.core_user USING btree (username varchar_pattern_ops);
CREATE UNIQUE INDEX core_user_username_key ON public.core_user USING btree (username);
CREATE INDEX core_user_groups_group_id_fe8c697f ON public.core_user_groups USING btree (group_id);
CREATE INDEX core_user_groups_user_id_70b4d9b8 ON public.core_user_groups USING btree (user_id);
CREATE UNIQUE INDEX core_user_groups_user_id_group_id_c82fcad1_uniq ON public.core_user_groups USING btree (user_id, group_id);
CREATE INDEX core_user_user_permissions_permission_id_35ccf601 ON public.core_user_user_permissions USING btree (permission_id);
CREATE INDEX core_user_user_permissions_user_id_085123d3 ON public.core_user_user_permissions USING btree (user_id);
CREATE UNIQUE INDEX core_user_user_permissions_user_id_permission_id_73ea0daa_uniq ON public.core_user_user_permissions USING btree (user_id, permission_id);
CREATE INDEX django_admin_log_content_type_id_c4bce8eb ON public.django_admin_log USING btree (content_type_id);
CREATE INDEX django_admin_log_user_id_c564eba6 ON public.django_admin_log USING btree (user_id);
CREATE UNIQUE INDEX django_content_type_app_label_model_76bd3d3b_uniq ON public.django_content_type USING btree (app_label, model);
CREATE INDEX django_session_expire_date_a5c62663 ON public.django_session USING btree (expire_date);
CREATE INDEX django_session_session_key_c0390e0f_like ON public.django_session USING btree (session_key varchar_pattern_ops);
CREATE INDEX patient_documents_patient_id_63d48cc0 ON public.patient_documents USING btree (patient_id);
CREATE INDEX patient_notes_patient_id_b22cf42e ON public.patient_notes USING btree (patient_id);
CREATE UNIQUE INDEX patients_pkey1 ON public.patients USING btree (id);

COMMIT;
