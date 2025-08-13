import { createBrainstormThread, getBrainstormMessages, sendBrainstormMessageStream } from '../services/brainstorm';
import { courseOutcomesService } from '../services/courseOutcomes';
// Import other services as needed

export const assetConfig = {
  'brainstorm': {
    title: 'Brainstorm',
    createThread: createBrainstormThread,
    getMessages: getBrainstormMessages,
    sendMessage: sendBrainstormMessageStream,
  },
  'course-outcomes': {
    title: 'Course Outcomes',
    createThread: courseOutcomesService.createThread,
    getMessages: courseOutcomesService.getMessages,
    sendMessage: courseOutcomesService.sendMessageStream,
  },
  // Add more features here...
};