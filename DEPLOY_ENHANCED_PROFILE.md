# Deployment Guide - Enhanced Profile Fields

## Quick Deployment Steps

### 1. Update Lambda Functions

#### Profile Handler Lambda
```bash
cd "Financial Helper App/lambda"
zip profile_handler.zip profile_handler.py
```

Then upload to AWS Lambda Console:
1. Go to AWS Lambda Console
2. Find `financial-helper-profile` function
3. Click "Upload from" → ".zip file"
4. Upload `profile_handler.zip`
5. Click "Save"

#### Advisor Handler Lambda
```bash
cd "Financial Helper App/lambda"
zip advisor_handler.zip advisor_handler.py
```

Then upload to AWS Lambda Console:
1. Go to AWS Lambda Console
2. Find `financial-helper-advisor` function
3. Click "Upload from" → ".zip file"
4. Upload `advisor_handler.zip`
5. Click "Save"

### 2. Update Frontend Files

The frontend files need to be deployed to Amplify:

```bash
cd "Financial Helper App"
git add frontend/index.html frontend/styles.css frontend/app.js
git commit -m "Add enhanced profile fields"
git push
```

Amplify will automatically detect the changes and deploy them.

**OR** manually upload via Amplify Console:
1. Go to AWS Amplify Console
2. Select your app
3. Go to "Hosting" → "Manual deploy"
4. Upload the `frontend` folder

### 3. Test the Changes

1. **Login to your app**
2. **Click "Edit Profile"**
3. **Verify new sections appear:**
   - Insurance Coverage
   - Emergency Fund & Liquidity
   - Additional Income Details
   - Investment Details
   - Detailed Debt Information
   - Tax & Benefits
   - Lifestyle & Future Planning
   - Retirement Planning

4. **Fill out some new fields**
5. **Click "Save Profile"**
6. **Verify fields are saved** (close and reopen modal)
7. **Ask a question** that uses the new data
8. **Verify AI uses the new information** in its response

### 4. Verify DynamoDB

Check that new fields are being stored:
1. Go to DynamoDB Console
2. Open `financial-helper-profiles` table
3. View an item
4. Confirm new fields are present

## Rollback Plan

If something goes wrong:

### Rollback Lambda
1. Go to Lambda Console
2. Click on the function
3. Go to "Versions" tab
4. Select previous version
5. Click "Actions" → "Publish new version"

### Rollback Frontend
```bash
git revert HEAD
git push
```

## Testing Checklist

- [ ] Profile modal opens correctly
- [ ] All new sections are visible
- [ ] Form fields have proper placeholders
- [ ] Helper text displays correctly
- [ ] Save button works
- [ ] Profile data persists after save
- [ ] Profile displays correctly in summary
- [ ] AI advisor receives new fields
- [ ] AI advice uses new information
- [ ] No console errors
- [ ] Mobile responsive design works

## Common Issues

### Issue: Fields not saving
**Solution:** Check CloudWatch logs for Lambda errors. Verify DynamoDB permissions.

### Issue: Modal too long
**Solution:** Modal is scrollable. This is expected with many fields.

### Issue: AI not using new fields
**Solution:** Check advisor Lambda logs. Verify profile data is being sent in request.

### Issue: Old profiles missing new fields
**Solution:** This is normal. New fields will be empty until user updates profile.

## Performance Notes

- **DynamoDB**: No schema changes needed (NoSQL)
- **Lambda**: No timeout changes needed
- **API Gateway**: No changes needed
- **Frontend**: Slightly larger form, but still fast

## Monitoring

After deployment, monitor:
1. **CloudWatch Logs** - Check for errors
2. **Lambda Metrics** - Verify execution times
3. **User Feedback** - Ask users about new fields
4. **DynamoDB Metrics** - Check read/write capacity

## Support

If you encounter issues:
1. Check CloudWatch logs first
2. Verify all files were uploaded correctly
3. Clear browser cache and test again
4. Check browser console for JavaScript errors

## Success Criteria

✅ Users can see and fill out new fields
✅ Data saves to DynamoDB correctly
✅ AI advisor uses new fields in advice
✅ No errors in CloudWatch logs
✅ Existing users' profiles still work
✅ Mobile experience is good

---

**Estimated Deployment Time:** 15-20 minutes
**Downtime:** None (rolling deployment)
**Risk Level:** Low (backward compatible)
