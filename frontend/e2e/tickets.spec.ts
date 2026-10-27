import {test, expect} from '@playwright/test'

const assessment = {category:'hvac',category_model_version:'0.1.0',category_provider:'sagemaker',
  urgency:'high',urgency_model_version:'0.1.0',urgency_provider:'sagemaker',recommended_priority:'high',
  confirmed_hazards:[],escalation_reasons:[],policy_version:'0.1.0',manual_review_required:true}
const draft = {assessment_id:'00000000-0000-0000-0000-000000000001',
  description:'The air conditioner is not cooling.',assessment,expires_at:1999999999}
const fixture = {ticket_id:'PP-20261026000000000000-1234abcd',assessment_id:draft.assessment_id,
  description:draft.description,property_label:'Browser Test Property',unit:'2B',assessment,status:'open',
  version:1,confirm_reviewed:true,created_at:'2026-10-26T12:00:00Z',updated_at:'2026-10-26T12:00:00Z'}
const reply = {reply:'An HVAC assessment is ready for manual review.',foundation_model:'test-only',ticket_draft:draft,
  tool_results:[{tool:'assess_maintenance',result:{category:'hvac',probabilities:{hvac:.7,plumbing:.1,electrical:.1,general:.1},provider:'sagemaker',model_version:'0.1.0',
    urgency_assessment:{urgency:'high',recommended_priority:'high',probabilities:{low:.1,medium:.1,high:.7,emergency:.1},provider:'sagemaker',model_version:'0.1.0',policy_version:'0.1.0',confirmed_hazards:[],escalation_reasons:[],manual_review_required:true}}}]}

test('reviewed ticket creation, persistence and status changes', async ({page}) => {
  let records: any[] = []; let creates=0
  await page.route('**/api/chat',route=>route.fulfill({json:reply}))
  await page.route('**/api/tickets**',async route=> {
    const method=route.request().method()
    if(method==='POST') {
      creates++; expect(route.request().postDataJSON().confirm_reviewed).toBe(true)
      records=[{...fixture}]; await route.fulfill({status:201,json:{ticket:records[0],replayed:false}})
    } else if(method==='PATCH') {
      const body=route.request().postDataJSON(); records[0]={...records[0],status:body.status,version:records[0].version+1}
      await route.fulfill({json:records[0]})
    } else await route.fulfill({json:{items:records,next_cursor:null}})
  })
  await page.goto('/')
  await page.getByRole('button',{name:'AC not cooling'}).click()
  await page.getByRole('button',{name:'Send request',exact:true}).click()
  await page.getByRole('button',{name:'Review & create ticket',exact:true}).click()
  const form=page.getByRole('form',{name:'Confirm maintenance ticket'})
  await expect(form.getByRole('button',{name:'Confirm & create ticket',exact:true})).toBeDisabled()
  await form.getByLabel('Property name',{exact:true}).fill('Browser Test Property')
  await form.getByLabel('Unit (optional)',{exact:true}).fill('2B')
  await form.getByRole('checkbox').check()
  await form.getByRole('button',{name:'Confirm & create ticket',exact:true}).click()
  await expect(page.getByText('Ticket saved',{exact:true})).toBeVisible()
  expect(creates).toBe(1)
  await page.keyboard.press('Escape')
  await page.reload()
  await page.getByRole('navigation').getByRole('button',{name:/^Tickets/}).click()
  await expect(page.getByText(fixture.ticket_id,{exact:true})).toBeVisible()
  await page.getByRole('button',{name:'Start work',exact:true}).click()
  await page.getByRole('button',{name:'Resolve ticket',exact:true}).click()
  await expect(page.getByRole('button',{name:'Resolve ticket',exact:true})).toHaveCount(0)
  await page.reload()
  await page.getByRole('navigation').getByRole('button',{name:/^Tickets/}).click()
  await expect(page.getByText('Resolved',{exact:true}).last()).toBeVisible()
})

test('failed confirmation keeps the same idempotency key',async ({page}) => {
  const keys: string[]=[]
  await page.route('**/api/chat',route=>route.fulfill({json:reply}))
  await page.route('**/api/tickets**',async route=> {
    if(route.request().method()==='GET') {await route.fulfill({json:{items:[],next_cursor:null}});return}
    keys.push(route.request().headers()['idempotency-key'])
    await route.fulfill(keys.length===1 ? {status:503,json:{detail:'Test write interrupted'}} : {status:200,json:{ticket:fixture,replayed:true}})
  })
  await page.goto('/')
  await page.getByRole('button',{name:'AC not cooling'}).click()
  await page.getByRole('button',{name:'Send request',exact:true}).click()
  await page.getByRole('button',{name:'Review & create ticket',exact:true}).click()
  const form=page.getByRole('form',{name:'Confirm maintenance ticket'})
  await form.getByLabel('Property name',{exact:true}).fill('Browser Test Property')
  await form.getByRole('checkbox').check()
  await form.getByRole('button',{name:'Confirm & create ticket',exact:true}).click()
  await expect(form.getByRole('alert')).toContainText('Test write interrupted')
  await form.getByRole('button',{name:'Confirm & create ticket',exact:true}).click()
  await expect(page.getByText('Ticket saved',{exact:true})).toBeVisible()
  expect(keys.length).toBe(2); expect(keys[0]).toBe(keys[1])
})
