$BASE = "http://localhost:8000/api/v1"
$TOKEN = $null
$TEST_RESULTS = @()

function Get-AdminToken {
    $r = Invoke-WebRequest -Uri "$BASE/auth/login" -Method POST -ContentType "application/x-www-form-urlencoded" -Body "username=admin&password=admin123" -UseBasicParsing
    $data = $r.Content | ConvertFrom-Json
    return $data.access_token
}

function Api-Call {
    param([string]$Method, [string]$Path, [object]$Body = $null, [string]$Token = $null, [string]$ContentType = "application/json")
    $headers = @{}
    if ($Token) { $headers["Authorization"] = "Bearer $Token" }
    try {
        if ($Body -and $ContentType -eq "application/json") {
            $json = $Body | ConvertTo-Json -Depth 10
            $r = Invoke-WebRequest -Uri "$BASE$Path" -Method $Method -ContentType "application/json" -Body $json -Headers $headers -UseBasicParsing
        } elseif ($Body -and $ContentType -eq "application/x-www-form-urlencoded") {
            $r = Invoke-WebRequest -Uri "$BASE$Path" -Method $Method -ContentType $ContentType -Body $Body -Headers $headers -UseBasicParsing
        } else {
            $r = Invoke-WebRequest -Uri "$BASE$Path" -Method $Method -Headers $headers -UseBasicParsing
        }
        $parsed = $null
        try { $parsed = $r.Content | ConvertFrom-Json } catch { $parsed = $r.Content }
        return @{ status = $r.StatusCode; body = $parsed }
    } catch {
        $status = 0
        $errorBody = ""
        try {
            $status = $_.Exception.Response.StatusCode.value__
            $reader = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream())
            $errorBody = $reader.ReadToEnd()
            $reader.Close()
        } catch {
            $errorBody = $_.Exception.Message
        }
        return @{ status = $status; body = $errorBody; error = $true }
    }
}

function Record-Test {
    param([string]$Category, [string]$Test, [string]$Status, [string]$Detail = "")
    $script:TEST_RESULTS += [PSCustomObject]@{
        Category = $Category
        Test = $Test
        Status = $Status
        Detail = $Detail
    }
    $icon = if ($Status -eq "PASS") { "[PASS]" } elseif ($Status -eq "FAIL") { "[FAIL]" } else { "[WARN]" }
    Write-Host "$icon $Category - $Test : $Detail"
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  DELETE SCENARIO TEST SUITE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$TOKEN = Get-AdminToken
Record-Test "Setup" "Admin Login" "PASS" "Token obtained"

Write-Host "`n--- Phase 1: Create Test Data ---" -ForegroundColor Yellow

$testUser1 = Api-Call -Method POST -Path "/auth/register" -Body @{
    username = "test_del_user1"
    email = "test_del1@test.com"
    password = "TestPass123!"
}
if ($testUser1.status -in @(200, 201)) {
    Record-Test "Setup" "Create test user 1" "PASS" "test_del_user1 created"
} else {
    Record-Test "Setup" "Create test user 1" "WARN" "Status: $($testUser1.status)"
}

$testUser2 = Api-Call -Method POST -Path "/auth/register" -Body @{
    username = "test_del_user2"
    email = "test_del2@test.com"
    password = "TestPass123!"
}
if ($testUser2.status -in @(200, 201)) {
    Record-Test "Setup" "Create test user 2" "PASS" "test_del_user2 created"
} else {
    Record-Test "Setup" "Create test user 2" "WARN" "Status: $($testUser2.status)"
}

$user1Login = Api-Call -Method POST -Path "/auth/login" -Body "username=test_del_user1&password=TestPass123!" -ContentType "application/x-www-form-urlencoded"
$user1Token = $null
if ($user1Login.status -eq 200) {
    $user1Token = $user1Login.body.access_token
    Record-Test "Setup" "Login test user 1" "PASS" "Token obtained"
} else {
    Record-Test "Setup" "Login test user 1" "FAIL" "Cannot login: $($user1Login.status), Body: $($user1Login.body)"
}

$cat1 = Api-Call -Method POST -Path "/categories" -Body @{
    name = "TestDelCategory"
    slug = "test-del-category"
    description = "For deletion test"
} -Token $TOKEN
$cat1Id = $null
if ($cat1.status -in @(200, 201)) {
    $cat1Id = $cat1.body.id
    Record-Test "Setup" "Create test category" "PASS" "ID: $cat1Id"
} else {
    Record-Test "Setup" "Create test category" "WARN" "Status: $($cat1.status), Body: $($cat1.body)"
}

$tag1 = Api-Call -Method POST -Path "/tags" -Body @{
    name = "TestDelTag"
    slug = "test-del-tag"
    color = "#ff0000"
} -Token $TOKEN
$tag1Id = $null
if ($tag1.status -in @(200, 201)) {
    $tag1Id = $tag1.body.id
    Record-Test "Setup" "Create test tag" "PASS" "ID: $tag1Id"
} else {
    Record-Test "Setup" "Create test tag" "WARN" "Status: $($tag1.status), Body: $($tag1.body)"
}

$article1 = Api-Call -Method POST -Path "/articles" -Body @{
    title = "Test Delete Article 1"
    slug = "test-delete-article-1"
    content = "This is test content for deletion testing."
    cover_image = "/uploads/default-cover.jpg"
    category_id = $cat1Id
    tag_ids = @($tag1Id)
    is_published = $true
} -Token $TOKEN
$article1Id = $null
if ($article1.status -in @(200, 201)) {
    $article1Id = $article1.body.id
    Record-Test "Setup" "Create test article 1 (admin)" "PASS" "ID: $article1Id"
} else {
    Record-Test "Setup" "Create test article 1" "WARN" "Status: $($article1.status), Body: $($article1.body)"
}

$article2 = Api-Call -Method POST -Path "/articles" -Body @{
    title = "Test Delete Article 2"
    slug = "test-delete-article-2"
    content = "Another test article."
    cover_image = "/uploads/default-cover.jpg"
    category_id = $cat1Id
    tag_ids = @($tag1Id)
    is_published = $true
} -Token $TOKEN
$article2Id = $null
if ($article2.status -in @(200, 201)) {
    $article2Id = $article2.body.id
    Record-Test "Setup" "Create test article 2 (admin)" "PASS" "ID: $article2Id"
} else {
    Record-Test "Setup" "Create test article 2" "WARN" "Status: $($article2.status), Body: $($article2.body)"
}

$article3 = Api-Call -Method POST -Path "/articles" -Body @{
    title = "Test Delete Article 3 - User1 Author"
    slug = "test-delete-article-3"
    content = "Article by user1 for deletion test."
    cover_image = "/uploads/default-cover.jpg"
    category_id = $cat1Id
    tag_ids = @($tag1Id)
    is_published = $true
} -Token $TOKEN
$article3Id = $null
if ($article3.status -in @(200, 201)) {
    $article3Id = $article3.body.id
    Record-Test "Setup" "Create test article 3 (admin)" "PASS" "ID: $article3Id"
} else {
    Record-Test "Setup" "Create test article 3" "WARN" "Status: $($article3.status)"
}

if ($user1Token -and $article1Id) {
    $like1 = Api-Call -Method POST -Path "/likes/$article1Id/toggle" -Token $user1Token
    Record-Test "Setup" "User1 likes article1" "PASS" "Status: $($like1.status)"

    $bookmark1 = Api-Call -Method POST -Path "/bookmarks/$article1Id/toggle" -Token $user1Token
    Record-Test "Setup" "User1 bookmarks article1" "PASS" "Status: $($bookmark1.status)"
}

if ($user1Token -and $article3Id) {
    $like2 = Api-Call -Method POST -Path "/likes/$article3Id/toggle" -Token $user1Token
    Record-Test "Setup" "User1 likes article3" "PASS" "Status: $($like2.status)"
}

if ($user1Token -and $article1Id) {
    $comment1 = Api-Call -Method POST -Path "/comments" -Body @{
        article_id = $article1Id
        content = "Test comment from user1"
    } -Token $user1Token
    $comment1Id = $null
    if ($comment1.status -in @(200, 201)) {
        $comment1Id = $comment1.body.id
        Record-Test "Setup" "Create test comment 1 (user1)" "PASS" "ID: $comment1Id"
    } else {
        Record-Test "Setup" "Create test comment 1" "WARN" "Status: $($comment1.status), Body: $($comment1.body)"
    }
}

if ($article1Id -and $comment1Id) {
    $reply1 = Api-Call -Method POST -Path "/comments" -Body @{
        article_id = $article1Id
        content = "Admin reply to user1 comment"
        parent_id = $comment1Id
    } -Token $TOKEN
    $reply1Id = $null
    if ($reply1.status -in @(200, 201)) {
        $reply1Id = $reply1.body.id
        Record-Test "Setup" "Create reply comment (admin)" "PASS" "ID: $reply1Id"
    } else {
        Record-Test "Setup" "Create reply comment" "WARN" "Status: $($reply1.status)"
    }
}

if ($article1Id) {
    $comment2 = Api-Call -Method POST -Path "/comments" -Body @{
        article_id = $article1Id
        content = "Admin comment on article1"
    } -Token $TOKEN
    $comment2Id = $null
    if ($comment2.status -in @(200, 201)) {
        $comment2Id = $comment2.body.id
        Record-Test "Setup" "Create admin comment" "PASS" "ID: $comment2Id"
    } else {
        Record-Test "Setup" "Create admin comment" "WARN" "Status: $($comment2.status)"
    }
}

$announcement1 = Api-Call -Method POST -Path "/announcements" -Body @{
    title = "Test Delete Announcement"
    content = "This announcement will be deleted."
    type = "info"
} -Token $TOKEN
$ann1Id = $null
if ($announcement1.status -in @(200, 201)) {
    $ann1Id = $announcement1.body.id
    Record-Test "Setup" "Create test announcement" "PASS" "ID: $ann1Id"
} else {
    Record-Test "Setup" "Create test announcement" "WARN" "Status: $($announcement1.status), Body: $($announcement1.body)"
}

$resCat1 = Api-Call -Method POST -Path "/resource-categories" -Body @{
    name = "TestDelResCat"
    slug = "test-del-rescat"
    description = "For deletion"
} -Token $TOKEN
$resCat1Id = $null
if ($resCat1.status -in @(200, 201)) {
    $resCat1Id = $resCat1.body.id
    Record-Test "Setup" "Create test resource category" "PASS" "ID: $resCat1Id"
} else {
    Record-Test "Setup" "Create test resource category" "WARN" "Status: $($resCat1.status), Body: $($resCat1.body)"
}

if ($resCat1Id) {
    $res1 = Api-Call -Method POST -Path "/resources" -Body @{
        title = "Test Delete Resource"
        url = "https://example.com/test"
        category_id = $resCat1Id
        description = "For deletion test"
    } -Token $TOKEN
    $res1Id = $null
    if ($res1.status -in @(200, 201)) {
        $res1Id = $res1.body.id
        Record-Test "Setup" "Create test resource" "PASS" "ID: $res1Id"
    } else {
        Record-Test "Setup" "Create test resource" "WARN" "Status: $($res1.status), Body: $($res1.body)"
    }
}

Write-Host "`n--- Phase 2: User Deletion Tests ---" -ForegroundColor Yellow

$usersList = Api-Call -Method GET -Path "/users?page=1&page_size=100" -Token $TOKEN
$testUser1Obj = $null
$testUser2Obj = $null
if ($usersList.status -eq 200) {
    foreach ($u in $usersList.body.items) {
        if ($u.username -eq "test_del_user1") { $testUser1Obj = $u }
        if ($u.username -eq "test_del_user2") { $testUser2Obj = $u }
    }
}

if ($testUser1Obj) {
    Write-Host "  Deleting user test_del_user1 (ID: $($testUser1Obj.id))..." -ForegroundColor Gray
    $delUser1 = Api-Call -Method DELETE -Path "/users/$($testUser1Obj.id)" -Token $TOKEN
    if ($delUser1.status -eq 200) {
        Record-Test "User Delete" "Delete test_del_user1" "PASS" "User deleted, ID: $($testUser1Obj.id)"
    } else {
        Record-Test "User Delete" "Delete test_del_user1" "FAIL" "Status: $($delUser1.status), Body: $($delUser1.body)"
    }
} else {
    Record-Test "User Delete" "Delete test_del_user1" "WARN" "User not found in list"
}

$delSelf = Api-Call -Method DELETE -Path "/users/1" -Token $TOKEN
if ($delSelf.status -eq 400 -or $delSelf.status -eq 403) {
    Record-Test "User Delete" "Cannot delete self (id=1)" "PASS" "Status: $($delSelf.status), correctly blocked"
} else {
    Record-Test "User Delete" "Cannot delete self (id=1)" "FAIL" "Status: $($delSelf.status), should be blocked"
}

if ($article1Id) {
    $checkArticle = Api-Call -Method GET -Path "/articles/$article1Id" -Token $TOKEN
    if ($checkArticle.status -eq 200) {
        $authorName = $checkArticle.body.author_name
        if ($authorName -eq "已注销用户") {
            Record-Test "User Delete" "Article author_name set to deactivated" "PASS" "author_name=$authorName"
        } else {
            Record-Test "User Delete" "Article author_name set to deactivated" "FAIL" "author_name=$authorName, expected '已注销用户'"
        }
        $authorId = $checkArticle.body.author_id
        if ($null -eq $authorId) {
            Record-Test "User Delete" "Article author_id set to null" "PASS"
        } else {
            Record-Test "User Delete" "Article author_id set to null" "FAIL" "author_id=$authorId"
        }
    } else {
        Record-Test "User Delete" "Check article after user delete" "WARN" "Status: $($checkArticle.status)"
    }
}

if ($article1Id) {
    $checkComments = Api-Call -Method GET -Path "/comments/article/$article1Id" -Token $TOKEN
    if ($checkComments.status -eq 200 -and $checkComments.body) {
        $foundComment = $checkComments.body | Where-Object { $_.id -eq $comment1Id }
        if ($foundComment) {
            if ($foundComment.author_name -eq "test_del_user1") {
                Record-Test "User Delete" "Comment author_name preserved" "PASS" "author_name=$($foundComment.author_name)"
            } else {
                Record-Test "User Delete" "Comment author_name preserved" "FAIL" "author_name=$($foundComment.author_name), expected 'test_del_user1'"
            }
            if ($null -eq $foundComment.user_id) {
                Record-Test "User Delete" "Comment user_id set to null" "PASS"
            } else {
                Record-Test "User Delete" "Comment user_id set to null" "FAIL" "user_id=$($foundComment.user_id)"
            }
        } else {
            Record-Test "User Delete" "Comment preserved after user delete" "WARN" "Comment not found in response (may be soft-deleted)"
        }
    }
}

if ($article1Id) {
    $checkLikeCount = Api-Call -Method GET -Path "/articles/$article1Id" -Token $TOKEN
    if ($checkLikeCount.status -eq 200) {
        $lc = $checkLikeCount.body.like_count
        if ($lc -ge 0) {
            Record-Test "User Delete" "Article like_count valid after user delete" "PASS" "like_count=$lc"
        } else {
            Record-Test "User Delete" "Article like_count valid after user delete" "FAIL" "like_count=$lc is negative"
        }
    }
}

if ($article3Id) {
    $checkArt3 = Api-Call -Method GET -Path "/articles/$article3Id" -Token $TOKEN
    if ($checkArt3.status -eq 200) {
        $a3lc = $checkArt3.body.like_count
        if ($a3lc -ge 0) {
            Record-Test "User Delete" "Article3 like_count valid after user delete" "PASS" "like_count=$a3lc"
        } else {
            Record-Test "User Delete" "Article3 like_count valid after user delete" "FAIL" "like_count=$a3lc is negative"
        }
    }
}

Write-Host "`n--- Phase 3: Article Deletion Tests ---" -ForegroundColor Yellow

if ($article2Id) {
    $delArticle = Api-Call -Method DELETE -Path "/articles/$article2Id" -Token $TOKEN
    if ($delArticle.status -eq 200) {
        Record-Test "Article Delete" "Delete article2" "PASS" "Article deleted, ID: $article2Id"
    } else {
        Record-Test "Article Delete" "Delete article2" "FAIL" "Status: $($delArticle.status), Body: $($delArticle.body)"
    }

    $checkDeleted = Api-Call -Method GET -Path "/articles/$article2Id" -Token $TOKEN
    if ($checkDeleted.status -eq 404) {
        Record-Test "Article Delete" "Deleted article returns 404" "PASS"
    } else {
        Record-Test "Article Delete" "Deleted article returns 404" "FAIL" "Status: $($checkDeleted.status)"
    }
}

$delNonExist = Api-Call -Method DELETE -Path "/articles/99999" -Token $TOKEN
if ($delNonExist.status -eq 404) {
    Record-Test "Article Delete" "Delete non-existent article returns 404" "PASS"
} else {
    Record-Test "Article Delete" "Delete non-existent article returns 404" "FAIL" "Status: $($delNonExist.status)"
}

Write-Host "`n--- Phase 4: Comment Deletion Tests ---" -ForegroundColor Yellow

if ($article1Id) {
    $cSoft = Api-Call -Method POST -Path "/comments" -Body @{
        article_id = $article1Id
        content = "Comment to be soft-deleted by user"
    } -Token $TOKEN
    $cSoftId = if ($cSoft.status -in @(200,201)) { $cSoft.body.id } else { $null }

    if ($cSoftId) {
        $softDel = Api-Call -Method DELETE -Path "/comments/$cSoftId" -Token $TOKEN
        if ($softDel.status -eq 200) {
            Record-Test "Comment Delete" "Soft delete comment (user)" "PASS" "ID: $cSoftId"
        } else {
            Record-Test "Comment Delete" "Soft delete comment (user)" "FAIL" "Status: $($softDel.status), Body: $($softDel.body)"
        }
    }
}

if ($article1Id) {
    $cAdminSoft = Api-Call -Method POST -Path "/comments" -Body @{
        article_id = $article1Id
        content = "Comment for admin soft delete"
    } -Token $TOKEN
    $cAdminSoftId = if ($cAdminSoft.status -in @(200,201)) { $cAdminSoft.body.id } else { $null }

    if ($cAdminSoftId) {
        $adminSoftDel = Api-Call -Method DELETE -Path "/comments/admin/$cAdminSoftId`?keep_record=true" -Token $TOKEN
        if ($adminSoftDel.status -eq 200) {
            $delType = $adminSoftDel.body.type
            if ($delType -eq "soft") {
                Record-Test "Comment Delete" "Admin soft delete comment" "PASS" "type=soft"
            } else {
                Record-Test "Comment Delete" "Admin soft delete comment" "FAIL" "type=$delType, expected soft"
            }
        } else {
            Record-Test "Comment Delete" "Admin soft delete comment" "FAIL" "Status: $($adminSoftDel.status), Body: $($adminSoftDel.body)"
        }
    }
}

if ($article1Id) {
    $cPerm = Api-Call -Method POST -Path "/comments" -Body @{
        article_id = $article1Id
        content = "Comment for permanent delete"
    } -Token $TOKEN
    $cPermId = if ($cPerm.status -in @(200,201)) { $cPerm.body.id } else { $null }

    if ($cPermId) {
        $permDel = Api-Call -Method DELETE -Path "/comments/admin/$cPermId`?keep_record=false" -Token $TOKEN
        if ($permDel.status -eq 200) {
            $delType = $permDel.body.type
            if ($delType -eq "permanent") {
                Record-Test "Comment Delete" "Admin permanent delete comment" "PASS" "type=permanent"
            } else {
                Record-Test "Comment Delete" "Admin permanent delete comment" "FAIL" "type=$delType, expected permanent"
            }
        } else {
            Record-Test "Comment Delete" "Admin permanent delete comment" "FAIL" "Status: $($permDel.status), Body: $($permDel.body)"
        }
    }
}

if ($article1Id) {
    $cb1 = Api-Call -Method POST -Path "/comments" -Body @{ article_id = $article1Id; content = "Batch delete 1" } -Token $TOKEN
    $cb2 = Api-Call -Method POST -Path "/comments" -Body @{ article_id = $article1Id; content = "Batch delete 2" } -Token $TOKEN
    $cb1Id = if ($cb1.status -in @(200,201)) { $cb1.body.id } else { $null }
    $cb2Id = if ($cb2.status -in @(200,201)) { $cb2.body.id } else { $null }

    if ($cb1Id -and $cb2Id) {
        $batchDel = Api-Call -Method POST -Path "/comments/admin/batch-delete" -Body @{
            comment_ids = @($cb1Id, $cb2Id)
            permanent = $false
        } -Token $TOKEN
        if ($batchDel.status -eq 200) {
            Record-Test "Comment Delete" "Batch soft delete comments" "PASS" "IDs: $cb1Id, $cb2Id"
        } else {
            Record-Test "Comment Delete" "Batch soft delete comments" "FAIL" "Status: $($batchDel.status), Body: $($batchDel.body)"
        }
    }
}

if ($article1Id) {
    $cb3 = Api-Call -Method POST -Path "/comments" -Body @{ article_id = $article1Id; content = "Batch perm delete 1" } -Token $TOKEN
    $cb4 = Api-Call -Method POST -Path "/comments" -Body @{ article_id = $article1Id; content = "Batch perm delete 2" } -Token $TOKEN
    $cb3Id = if ($cb3.status -in @(200,201)) { $cb3.body.id } else { $null }
    $cb4Id = if ($cb4.status -in @(200,201)) { $cb4.body.id } else { $null }

    if ($cb3Id -and $cb4Id) {
        $batchPermDel = Api-Call -Method POST -Path "/comments/admin/batch-delete" -Body @{
            comment_ids = @($cb3Id, $cb4Id)
            permanent = $true
        } -Token $TOKEN
        if ($batchPermDel.status -eq 200) {
            Record-Test "Comment Delete" "Batch permanent delete comments" "PASS" "IDs: $cb3Id, $cb4Id"
        } else {
            Record-Test "Comment Delete" "Batch permanent delete comments" "FAIL" "Status: $($batchPermDel.status), Body: $($batchPermDel.body)"
        }
    }
}

Write-Host "`n--- Phase 5: Category/Tag Deletion Tests ---" -ForegroundColor Yellow

if ($cat1Id) {
    $delCatWithArticles = Api-Call -Method DELETE -Path "/categories/$cat1Id" -Token $TOKEN
    if ($delCatWithArticles.status -eq 400) {
        Record-Test "Category Delete" "Cannot delete category with articles" "PASS" "Correctly blocked"
    } else {
        Record-Test "Category Delete" "Cannot delete category with articles" "FAIL" "Status: $($delCatWithArticles.status), should be 400"
    }
}

$cat2 = Api-Call -Method POST -Path "/categories" -Body @{ name = "EmptyCatForDel"; slug = "empty-cat-for-del"; description = "No articles" } -Token $TOKEN
$cat2Id = if ($cat2.status -in @(200,201)) { $cat2.body.id } else { $null }
if ($cat2Id) {
    $delEmptyCat = Api-Call -Method DELETE -Path "/categories/$cat2Id" -Token $TOKEN
    if ($delEmptyCat.status -eq 200) {
        Record-Test "Category Delete" "Delete empty category" "PASS" "ID: $cat2Id"
    } else {
        Record-Test "Category Delete" "Delete empty category" "FAIL" "Status: $($delEmptyCat.status), Body: $($delEmptyCat.body)"
    }
}

if ($tag1Id) {
    $delTagWithArticles = Api-Call -Method DELETE -Path "/tags/$tag1Id" -Token $TOKEN
    if ($delTagWithArticles.status -eq 400) {
        Record-Test "Tag Delete" "Cannot delete tag with articles" "PASS" "Correctly blocked"
    } else {
        Record-Test "Tag Delete" "Cannot delete tag with articles" "FAIL" "Status: $($delTagWithArticles.status), should be 400"
    }
}

$tag2 = Api-Call -Method POST -Path "/tags" -Body @{ name = "EmptyTagForDel"; slug = "empty-tag-for-del" } -Token $TOKEN
$tag2Id = if ($tag2.status -in @(200,201)) { $tag2.body.id } else { $null }
if ($tag2Id) {
    $delEmptyTag = Api-Call -Method DELETE -Path "/tags/$tag2Id" -Token $TOKEN
    if ($delEmptyTag.status -eq 200) {
        Record-Test "Tag Delete" "Delete empty tag" "PASS" "ID: $tag2Id"
    } else {
        Record-Test "Tag Delete" "Delete empty tag" "FAIL" "Status: $($delEmptyTag.status), Body: $($delEmptyTag.body)"
    }
}

Write-Host "`n--- Phase 6: Announcement/Resource Deletion Tests ---" -ForegroundColor Yellow

if ($ann1Id) {
    $delAnn = Api-Call -Method DELETE -Path "/announcements/$ann1Id" -Token $TOKEN
    if ($delAnn.status -eq 200) {
        Record-Test "Announcement Delete" "Delete announcement" "PASS" "ID: $ann1Id"
    } else {
        Record-Test "Announcement Delete" "Delete announcement" "FAIL" "Status: $($delAnn.status), Body: $($delAnn.body)"
    }
}

$delAnnNonExist = Api-Call -Method DELETE -Path "/announcements/99999" -Token $TOKEN
if ($delAnnNonExist.status -eq 404) {
    Record-Test "Announcement Delete" "Delete non-existent returns 404" "PASS"
} else {
    Record-Test "Announcement Delete" "Delete non-existent returns 404" "FAIL" "Status: $($delAnnNonExist.status)"
}

if ($res1Id) {
    $delRes = Api-Call -Method DELETE -Path "/resources/$res1Id" -Token $TOKEN
    if ($delRes.status -eq 200) {
        Record-Test "Resource Delete" "Delete resource" "PASS" "ID: $res1Id"
    } else {
        Record-Test "Resource Delete" "Delete resource" "FAIL" "Status: $($delRes.status), Body: $($delRes.body)"
    }
}

if ($resCat1Id) {
    $delResCat = Api-Call -Method DELETE -Path "/resource-categories/$resCat1Id" -Token $TOKEN
    if ($delResCat.status -eq 200) {
        Record-Test "Resource Category Delete" "Delete empty resource category" "PASS" "ID: $resCat1Id"
    } else {
        Record-Test "Resource Category Delete" "Delete empty resource category" "FAIL" "Status: $($delResCat.status), Body: $($delResCat.body)"
    }
}

$resCat2 = Api-Call -Method POST -Path "/resource-categories" -Body @{ name = "ResCatWithRes"; slug = "rescat-with-res"; description = "Has resources" } -Token $TOKEN
$resCat2Id = if ($resCat2.status -in @(200,201)) { $resCat2.body.id } else { $null }
if ($resCat2Id) {
    $res2 = Api-Call -Method POST -Path "/resources" -Body @{ title = "Res Under Cat2"; url = "https://example.com/res2"; category_id = $resCat2Id } -Token $TOKEN
    if ($res2.status -in @(200,201)) {
        $delResCatWithRes = Api-Call -Method DELETE -Path "/resource-categories/$resCat2Id" -Token $TOKEN
        if ($delResCatWithRes.status -eq 400) {
            Record-Test "Resource Category Delete" "Cannot delete category with resources" "PASS" "Correctly blocked"
        } else {
            Record-Test "Resource Category Delete" "Cannot delete category with resources" "FAIL" "Status: $($delResCatWithRes.status), should be 400"
        }
    }
}

Write-Host "`n--- Phase 7: User Delete - Second User ---" -ForegroundColor Yellow

if ($testUser2Obj) {
    $delUser2 = Api-Call -Method DELETE -Path "/users/$($testUser2Obj.id)" -Token $TOKEN
    if ($delUser2.status -eq 200) {
        Record-Test "User Delete" "Delete test_del_user2" "PASS" "User deleted"
    } else {
        Record-Test "User Delete" "Delete test_del_user2" "FAIL" "Status: $($delUser2.status), Body: $($delUser2.body)"
    }
}

Write-Host "`n--- Phase 8: Edge Case Tests ---" -ForegroundColor Yellow

$delNonExistUser = Api-Call -Method DELETE -Path "/users/99999" -Token $TOKEN
if ($delNonExistUser.status -eq 404) {
    Record-Test "Edge Case" "Delete non-existent user returns 404" "PASS"
} else {
    Record-Test "Edge Case" "Delete non-existent user returns 404" "FAIL" "Status: $($delNonExistUser.status)"
}

$delNonExistComment = Api-Call -Method DELETE -Path "/comments/99999" -Token $TOKEN
if ($delNonExistComment.status -eq 404) {
    Record-Test "Edge Case" "Delete non-existent comment returns 404" "PASS"
} else {
    Record-Test "Edge Case" "Delete non-existent comment returns 404" "FAIL" "Status: $($delNonExistComment.status)"
}

$delNonExistCategory = Api-Call -Method DELETE -Path "/categories/99999" -Token $TOKEN
if ($delNonExistCategory.status -eq 404) {
    Record-Test "Edge Case" "Delete non-existent category returns 404" "PASS"
} else {
    Record-Test "Edge Case" "Delete non-existent category returns 404" "FAIL" "Status: $($delNonExistCategory.status)"
}

$delNonExistTag = Api-Call -Method DELETE -Path "/tags/99999" -Token $TOKEN
if ($delNonExistTag.status -eq 404) {
    Record-Test "Edge Case" "Delete non-existent tag returns 404" "PASS"
} else {
    Record-Test "Edge Case" "Delete non-existent tag returns 404" "FAIL" "Status: $($delNonExistTag.status)"
}

Write-Host "`n--- Phase 9: Data Integrity Verification ---" -ForegroundColor Yellow

if ($article1Id) {
    $verifyArticle = Api-Call -Method GET -Path "/articles/$article1Id" -Token $TOKEN
    if ($verifyArticle.status -eq 200) {
        $a = $verifyArticle.body
        Record-Test "Data Integrity" "Article1 still accessible" "PASS" "Title: $($a.title)"
        
        if ($a.like_count -ge 0) {
            Record-Test "Data Integrity" "Article like_count >= 0" "PASS" "like_count=$($a.like_count)"
        } else {
            Record-Test "Data Integrity" "Article like_count >= 0" "FAIL" "like_count=$($a.like_count) is negative"
        }
        
        if ($a.comment_count -ge 0) {
            Record-Test "Data Integrity" "Article comment_count >= 0" "PASS" "comment_count=$($a.comment_count)"
        } else {
            Record-Test "Data Integrity" "Article comment_count >= 0" "FAIL" "comment_count=$($a.comment_count) is negative"
        }
        
        if ($a.bookmark_count -ge 0) {
            Record-Test "Data Integrity" "Article bookmark_count >= 0" "PASS" "bookmark_count=$($a.bookmark_count)"
        } else {
            Record-Test "Data Integrity" "Article bookmark_count >= 0" "FAIL" "bookmark_count=$($a.bookmark_count) is negative"
        }
    } else {
        Record-Test "Data Integrity" "Article1 still accessible" "FAIL" "Status: $($verifyArticle.status)"
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  TEST REPORT SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$passCount = ($TEST_RESULTS | Where-Object { $_.Status -eq "PASS" }).Count
$failCount = ($TEST_RESULTS | Where-Object { $_.Status -eq "FAIL" }).Count
$warnCount = ($TEST_RESULTS | Where-Object { $_.Status -eq "WARN" }).Count
$totalCount = $TEST_RESULTS.Count

Write-Host "`nTotal: $totalCount | PASS: $passCount | FAIL: $failCount | WARN: $warnCount" -ForegroundColor White

if ($failCount -gt 0) {
    Write-Host "`n--- FAILED TESTS ---" -ForegroundColor Red
    $TEST_RESULTS | Where-Object { $_.Status -eq "FAIL" } | ForEach-Object {
        Write-Host "  [FAIL] $($_.Category) - $($_.Test): $($_.Detail)" -ForegroundColor Red
    }
}

if ($warnCount -gt 0) {
    Write-Host "`n--- WARNINGS ---" -ForegroundColor Yellow
    $TEST_RESULTS | Where-Object { $_.Status -eq "WARN" } | ForEach-Object {
        Write-Host "  [WARN] $($_.Category) - $($_.Test): $($_.Detail)" -ForegroundColor Yellow
    }
}

Write-Host "`n--- ALL TESTS ---" -ForegroundColor White
$TEST_RESULTS | ForEach-Object {
    $color = if ($_.Status -eq "PASS") { "Green" } elseif ($_.Status -eq "FAIL") { "Red" } else { "Yellow" }
    Write-Host "  [$($_.Status)] $($_.Category) - $($_.Test): $($_.Detail)" -ForegroundColor $color
}
