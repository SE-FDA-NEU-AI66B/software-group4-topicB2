# EduSurvey: Neon production handoff — 2026-11-16

## Đích đã được cấp quyền

- Project hiện có: `steep-firefly-83236241` (EduSurvey).
- Branch `main`: `br-autumn-tooth-bd5zwmh1`.
- Database: `edusurvey`; owner: `edusurvey_owner`; PostgreSQL 18.7.
- Project ở `aws-us-east-2`; không tạo project/branch/compute mới hoặc đổi region.
- Trước migration đã xác minh database/user/schema, TLS client và **0 relations**
  trong public. Chỉ migration version 1 của repository được áp dụng.
- Seed synthetic đã commit **một lần**, từ SQLite mới trong TemporaryDirectory.
  Không đọc, copy hoặc upload `data/edusurvey.db`.

Manifest sau seed: users 6, courses 5, course_enrollments 7,
course_lecturers 5, evaluations 10, questions 30, responses 6,
response_answers 14, deadline_reminders 0. Không chạy lại seed trên đích này.
Migration chạy lại chỉ kiểm version/checksum; startup không migrate/seed.

## Code, PR và review

Main remote kiểm tra trực tiếp: `6fa42b65ed74707b265f0659591c42875eb8abc5`;
[main CI](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/actions/runs/43819318304)
đã xanh. Main chưa chứa stack PostgreSQL.

Thứ tự dependency:

1. [#244 core](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/244)
   → main; reviewer đã yêu cầu: `toantran249`.
2. [#245 integration](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/245)
   → branch của #244; reviewer: `tlduongducanh281-jpg`.
3. [#246 hosting/runbook](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/pull/246)
   → branch của #245; reviewer: `toantran249`.

Đã chuyển cả ba từ draft sang ready for review, chưa có approval/merge.
CI #245 trước đây fail do test startup đã được thêm trước implementation
PostgreSQL trong `tools/prepare_production.py`. Commit `961d03d` đưa chính
implementation đã có ở #246 vào #245, không sửa assertion hoặc tests cũ;
54 integration/production cases pass trên localhost, CI #245 sau sửa xanh:
[run 43838551831](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/actions/runs/43838551831).
Patch đã merge vào branch #246 bằng merge thường, không merge PR vào main.

Reviewer cần review diff thực chất. Sau approval và green checks, teammate
merge theo thứ tự trên; retarget/sync PR kế tiếp về main và chờ CI của HEAD
mới trước merge. Check “Someone else must review” xanh không thay approval.
Không bật deployment flag khi stack chưa được review/merge và main chưa xanh.

CI #246 tại commit tích hợp `da6fc76971b5c860d7a5dc2447e141c855ea72ba`
đã xanh: [run 43838682207](https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2/actions/runs/43838682207).
Commit cập nhật tài liệu sau đó cần CI mới trước merge. Main rules read-back có
yêu cầu một approval, cấm force-push/xóa branch; không thấy required-status-check
rule trong endpoint này. Actor có push nhưng không có admin; không sửa protections.

## Kết quả kiểm chứng lần này

- Full regression: **359 passed trong 133,32s**, zero failures/errors/skips;
  PostgreSQL 16 localhost dedicated và Chrome thật ở laptop/phone. Tests SQLite,
  UI, requirements và historical evidence cũ không bị sửa.
- [Console mới](evidence/neon-production-20261116/pytest.txt),
  [JUnit mới](evidence/neon-production-20261116/pytest.xml).
- Ruff toàn repo và `git diff --check` pass.
- [Neon verification JSON](evidence/neon-production-20261116/neon-verification.json):
  real direct/pooled TLS (libpq `ssl_in_use`), đúng database/role/schema,
  migration checksum/idempotence và đủ 9 bảng; 12 FK validated, 0 orphan rows.
  `pg_stat_ssl` sau proxy Neon không phải bằng chứng TLS phía client; kiểm bằng
  thuộc tính libpq của chính client đã kết nối.
- Xác minh hash/password của cả 6 synthetic accounts; login thật đủ student,
  lecturer và administrator. Không xuất password/hash vào evidence.
- Production Flask test client với HTTPS base URL và pooled Neon thật chạy đủ
  **US01 login, US02 list/questions, US03 submit/duplicate/reload,
  US04 lecturer feedback/role isolation, US11 logout/denied access**.
- US03 chuyển **draft student2/evaluation1** thành submitted: response ID `2`,
  đủ 3 answers; duplicate trả 409; lecturer thấy đúng response/comment synthetic.
  Không xóa/reset response sau kiểm thử. Slot student1/evaluation1 vẫn chưa trả lời.
  Sau smoke: responses vẫn 6, response_answers tăng từ 14 lên 16.
- `/health` trả 200 và đúng JSON trên kết nối pooled thật. Hai lần chạy
  `tools.prepare_production` trong **hai Python process mới** đều thành công;
  hash nội dung cả 9 bảng không đổi sau mỗi lần. Migration reapplied cũng không
  đổi hash. Đây là kiểm process local với Neon thật, chưa phải restart Render.

Các kết quả này không chứng nhận HTTPS public, thời gian phản hồi từ Render,
Render restart/redeploy, backup/restore hoặc live browser acceptance. Những
kiểm tra đó cần service thật sau review và green main CI. Chưa deploy tài nguyên
nào hoặc tạo tài nguyên trả phí trong lần thực hiện này.

## Lấy và cấu hình secrets khi cần một terminal/VS Code mới

Phiên quản trị hiện tại đã lấy được cả direct và pooled URL mà không in chúng.
Không gửi URL/password vào chat. Không đưa URL vào command arguments, terminal
history, screenshot hoặc Git. Không thay driver/requirements cũ; cài dependency
PostgreSQL bằng file riêng đã có.

Trong [Neon Console](https://console.neon.tech), mở đúng project EduSurvey →
**Connect** → chọn branch `main`, database `edusurvey`, role `edusurvey_owner`.
**Connection pooling OFF**: copy direct URL cho `DIRECT_URL`.
**Connection pooling ON**: copy pooled URL cho `DATABASE_URL`.
Giữ tham số TLS do Neon cung cấp; direct hostname không có `-pooler`, pooled có.
[Quy tắc pooled/direct chính thức](https://neon.com/docs/connect/connection-pooling.md).

Trong integrated terminal tại repo, chạy đoạn dưới. Hai prompt ẩn nhận URL
trực tiếp từ clipboard; giá trị không xuất hiện trong lệnh/history. Đoạn này
tạo file mới với quyền 0600, từ chối ghi đè file có sẵn và kiểm `.gitignore`.
File chỉ được load khi bạn chủ động source; terminal local bình thường vẫn SQLite.

```bash
python - <<'PY'
import getpass
import os
import shlex
import subprocess
from urllib.parse import parse_qs, urlsplit

path = '.env.neon.local'
assert subprocess.run(['git', 'check-ignore', '-q', path]).returncode == 0
values = {}
for key, pooled in [('DIRECT_URL', False), ('DATABASE_URL', True)]:
    value = getpass.getpass(key + ' (hidden): ')
    parsed = urlsplit(value)
    assert parsed.scheme in {'postgres', 'postgresql'}
    assert parsed.path == '/edusurvey' and parsed.hostname
    assert ('-pooler' in parsed.hostname) == pooled
    assert parse_qs(parsed.query).get('sslmode', [''])[0] in {'require', 'verify-ca', 'verify-full'}
    values[key] = value
fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, 'w') as out:
    for key, value in values.items():
        out.write(key + '=' + shlex.quote(value) + '\n')
print('Private environment saved; no credentials displayed.')
PY
```

Để sử dụng trong **terminal riêng chỉ dành cho Neon**:

```bash
set -a
source .env.neon.local
set +a
python -m pip install -r requirements-postgres.txt
```

Không chạy seed lại; database này đã seed. Không chạy pytest với runtime URL.
Tests chỉ nhận `EDUSURVEY_TEST_POSTGRES_URL` trỏ database localhost dedicated có
prefix `edusurvey_test`; guard trong fixture từ chối Neon. Khi xong dùng
`unset DIRECT_URL DATABASE_URL` hoặc đóng terminal để quay về SQLite local.
Trong VS Code debugger, chọn `envFile` trỏ `${workspaceFolder}/.env.neon.local`
chỉ cho cấu hình debug Neon riêng; không thêm file env vào Git và không bật
logging environment. VS Code không tự load file này cho tất cả terminal.

## Render Web Service đã chuẩn bị, chưa provision/deploy

Render plugin được tìm thấy nhưng chưa kết nối; không có `RENDER_API_KEY` hoặc
`RENDER_SERVICE_ID` trong terminal. GitHub chưa có repository variables,
Actions secrets hoặc environment deployment được liệt kê tại lúc kiểm tra.
Không suy ra rằng tài khoản Render không có service; chưa có quyền kiểm tra.

`render.yaml` đã chuẩn bị Python Web Service **Free**, Singapore, branch main,
một instance, không disk hoặc Render database; không tạo thêm Neon resource.
Auto-deploy `off`; build `pip install -r requirements-postgres.txt`; start
`python -m tools.prepare_production && gunicorn --config gunicorn.conf.py src.app:app`;
health `/health`. Không dùng runbook paid-disk/SQLite lịch sử cho cấu hình này.

Sau khi quyền Render đã kết nối, phải kiểm service hiện có và plan trước khi
tạo gì. Không bấm Create/Deploy Blueprint khi code chưa review/merge: việc tạo
service lần đầu có thể khởi động deployment, kể cả auto-deploy off.

Trên **service đúng**, Environment → Add Environment Variable:

| Key | Value / xử lý |
| --- | --- |
| `EDUSURVEY_ENV` | `production` |
| `EDUSURVEY_DATABASE_BACKEND` | `postgresql` |
| `DATABASE_URL` | Pooled URL từ đúng Neon Connect, paste trực tiếp vào secret field |
| `EDUSURVEY_SECRET_KEY` | Secret ngẫu nhiên ổn định >=32 ký tự; Blueprint generate một lần, không xoay mỗi restart |
| `PYTHON_VERSION` | Theo Blueprint hiện tại |

Chọn **Save only** để lưu env mà chưa deploy. Không cần `DIRECT_URL` trên web
service; không cấu hình `EDUSURVEY_BOOTSTRAP_DEMO` hoặc SQLite mount.
[Render env và Save only](https://render.com/docs/configure-environment-variables).
Không copy secrets vào YAML/README hoặc GitHub Variables.

## CI-gated release và kiểm tra sau restart

Workflow hiện có yêu cầu full Python tests + secret checks + CI gate; deploy
chỉ trên push main, `needs: [gate]`, `RENDER_DEPLOY_ENABLED=true` và environment
`production`. Script deploy kiểm repo/main, platform auto-deploy off, main SHA
chưa bị thay thế, gửi đúng commitId, đối chiếu live SHA và HTTPS `/health`.

Khi service thực tế đã được xác minh và cho phép deploy, cấu hình GitHub:
repository Variable `RENDER_SERVICE_ID` là ID thật; secret `RENDER_API_KEY`
trong environment `production`; `RENDER_DEPLOY_ENABLED=false` cho đến khi gate
database/code và review hoàn tất. Không đưa database URL vào CI tests.
Admin cần kiểm required checks và environment protections; quyền hiện tại
không cho phép chứng nhận các protections chưa được read-back.

Trước release, ghi ID/status/answers của response synthetic kiểm thử. Sau
release, kiểm HTTPS `/health` = 200 với `{"status":"ok","database":"ok"}`,
chạy đủ US01/02/03/04/11 trên browser private ở laptop/phone. Reload, restart
**Render Web Service**, rồi đối chiếu cùng response/answers/deadline và feedback
lecturer. Restart không được seed/migrate/reset dữ liệu. Ghi provider deploy ID,
full SHA và thời gian. Thử này chưa thể thực hiện khi chưa có host/quyền Render.

Chỉ điền URL HTTPS nộp M5 sau khi host có thật và kiểm tra trên thành công;
không suy đoán hostname hoặc gọi local test là public acceptance.
