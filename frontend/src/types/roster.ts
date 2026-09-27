import type { Enrollment } from './enrollment'
export interface RosterEntry extends Enrollment {
  student_number: string
  first_name: string
  last_name: string
}
